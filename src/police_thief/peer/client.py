"""The peer's FastMCP client.

Written against **fastmcp 3.4.5**: ``Client(transport)`` where transport is
either a URL string (HTTP) or a :class:`FastMCP` instance (in-memory, used by
tests), and ``client.call_tool(name, arguments)`` returning a
``CallToolResult`` whose ``.data`` holds the structured reply. Failures raise
``fastmcp.exceptions.ToolError``.

Every call is bounded three ways: admitted by the Gatekeeper, deadlined by
``response_timeout_sec``, and retried at most ``max_retries`` times with
``retry_backoff_sec`` between attempts. Nothing here retries forever, and
nothing here retries a validation failure -- resending a malformed message
produces the same rejection and spends rate budget for nothing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Mapping

from fastmcp import Client
from fastmcp.exceptions import ToolError

from police_thief.peer.clock import Clock, SystemClock
from police_thief.peer.deadline import DeadlineTracker, RetryPolicy
from police_thief.peer.events import EventSink, NullEventSink
from police_thief.peer.gatekeeper import Gatekeeper
from police_thief.protocol.codec import decode_mapping
from police_thief.protocol.exceptions import (
    InvalidResponseError,
    PeerProtocolError,
    PeerUnavailableError,
    ProtocolError,
)
from police_thief.protocol.messages import Envelope


@dataclass(frozen=True, slots=True)
class CallOutcome:
    """The structured result of one protocol call."""

    ok: bool
    envelope: Envelope | None = None
    error: str | None = None
    detail: str | None = None
    retryable: bool = False

    @property
    def rejected(self) -> bool:
        """True when the opponent validly refused the message.

        Distinct from a transport failure: a rejection means the message
        arrived and was understood well enough to be refused, so resending it
        unchanged is pointless.
        """
        return not self.ok and self.error is not None


class PeerClient:
    """Calls the opponent's FastMCP tools."""

    def __init__(
        self,
        transport: Any,
        *,
        gatekeeper: Gatekeeper,
        retry_policy: RetryPolicy,
        clock: Clock | None = None,
        events: EventSink | None = None,
    ) -> None:
        self._transport = transport
        self._gatekeeper = gatekeeper
        self._policy = retry_policy
        self._clock = clock or SystemClock()
        self._events = events or NullEventSink()
        self._client: Client | None = None
        # One MCP session, one caller at a time. Both peers call each other at
        # the same moment during commit and reveal, and overlapping requests on
        # a shared session stall until the response deadline -- which surfaced
        # as "opponent commitment never arrived" several turns in.
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Raw tool call
    # ------------------------------------------------------------------

    async def _session(self) -> Client:
        """Return a live client, connecting once and reusing it.

        A fresh ``Client`` per message would open and tear down an MCP session
        for every call (POST, GET, DELETE each time). Beyond being wasteful,
        that serialises traffic badly when both peers call each other at the
        same moment -- which is exactly what the commit and reveal phases do.
        """
        if self._client is None:
            client = Client(self._transport)
            await client.__aenter__()
            self._client = client
        return self._client

    async def aclose(self) -> None:
        """Close the persistent session, if one is open."""
        client, self._client = self._client, None
        if client is not None:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                # Teardown must not raise during shutdown.
                pass

    async def _call_tool_once(
        self, tool: str, arguments: Mapping[str, Any]
    ) -> Any:
        """One attempt, with no retry and no admission control.

        Wrapped by :meth:`_guarded` which adds both.
        """
        try:
            # One persistent session, one caller at a time.
            #
            # Both alternatives were measured and are worse. A fresh Client per
            # message opens and tears down an MCP session for every call and
            # fails on turn 1. An unguarded shared session lets the commit and
            # reveal calls -- which both peers issue at the same moment --
            # overlap on one session, where they stall until the response
            # deadline and surface as "opponent commitment never arrived".
            async with self._lock:
                client = await self._session()
                result = await client.call_tool(tool, dict(arguments))
        except ToolError as exc:
            # The tool exists but refused, or does not exist. Not retryable.
            raise InvalidResponseError(
                f"tool {tool!r} rejected the call: {exc}"
            ) from exc
        except (ConnectionError, OSError) as exc:
            await self.aclose()  # a broken session must not be reused
            raise PeerUnavailableError(
                f"could not reach the opponent: {type(exc).__name__}: {exc}"
            ) from exc
        except Exception as exc:
            await self.aclose()
            # httpx and anyio raise their own families; treat an unrecognised
            # transport failure as "peer unreachable" and let the bounded retry
            # decide, rather than crashing the peer.
            raise PeerUnavailableError(
                f"transport failure calling {tool!r}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if getattr(result, "is_error", False):
            raise InvalidResponseError(f"tool {tool!r} returned an error result")

        data = getattr(result, "data", None)
        if data is None:
            data = getattr(result, "structured_content", None)
        if not isinstance(data, dict):
            raise InvalidResponseError(
                f"tool {tool!r} returned {type(data).__name__}, expected an object"
            )
        return data

    async def _guarded(
        self, tool: str, arguments: Mapping[str, Any], *, description: str
    ) -> Any:
        """One admitted, deadlined, bounded-retry call."""
        tracker = DeadlineTracker(self._policy, self._clock)

        async def attempt() -> Any:
            async with self._gatekeeper.slot():
                return await self._call_tool_once(tool, arguments)

        try:
            return await tracker.run(attempt, description=description)
        finally:
            for record in tracker.attempts:
                if record.error:
                    self._events.emit(
                        "retry",
                        operation=description,
                        attempt=record.attempt,
                        error=record.error,
                    )

    # ------------------------------------------------------------------
    # Protocol operations
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Is the opponent's server up?

        Returns ``False`` rather than raising when unreachable: during startup
        the opponent legitimately may not exist yet, and the two processes
        start independently with no ordering guarantee.
        """
        try:
            data = await self._call_tool_once("health_check", {})
        except PeerProtocolError:
            return False
        return bool(data.get("ok"))

    async def send(self, envelope: Envelope) -> CallOutcome:
        """Send a protocol message and interpret the reply.

        The same ``message_id`` is preserved across retries, which is what
        makes a retry idempotent at the far end: the opponent's registry
        recognises the repeat and returns its cached reply instead of acting
        twice.
        """
        self._events.emit(
            "outbound_message",
            message_type=envelope.message_type.value,
            message_id=envelope.message_id,
        )

        data = await self._guarded(
            "receive_protocol_message",
            {"envelope": envelope.to_wire()},
            description=f"{envelope.message_type.value} message",
        )
        return self._interpret(data)

    def _interpret(self, data: Mapping[str, Any]) -> CallOutcome:
        if not data.get("ok", False):
            return CallOutcome(
                ok=False,
                error=str(data.get("error", "UnknownError")),
                detail=str(data.get("detail", ""))[:500],
                retryable=bool(data.get("retryable", False)),
            )

        raw = data.get("envelope")
        if raw is None:
            return CallOutcome(ok=True)

        try:
            return CallOutcome(ok=True, envelope=decode_mapping(raw))
        except ProtocolError as exc:
            raise InvalidResponseError(
                f"opponent replied with an invalid envelope: {exc}"
            ) from exc
