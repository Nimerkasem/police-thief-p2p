"""The peer orchestrator: single gateway to all sub-systems (E-3).

Ch. 8 (PDF p. 78) defines the role precisely: a central component that
initialises connections, drives the decision module, coordinates between
components and talks to the log managers -- but *"contains no decision logic or
low-level communication of its own. Its job is to coordinate, not to execute."*

So this class owns the lifecycle and the state machine, and delegates
everything else. It has no FastMCP parsing (that is
:mod:`police_thief.peer.server`), no game rules (that is the domain), and no
strategy (Phase 3).

Everything is injected -- transport, clock, id generator, event sink, config,
state machine -- because a peer that constructs its own dependencies cannot be
tested without a network, and an untestable handshake is one that gets debugged
during a league match.

What it must never do
---------------------
Store the opponent's true position, act as a referee, decide strategy, or
bypass ``LocalState``. It holds a ``LocalState`` for its own role and never
receives one for the other. Asserted by
``tests/peer/test_information_boundary.py::test_orchestrator_has_no_global_state_field``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from police_thief.config.hashing import config_sha256
from police_thief.config.models import PrivateConfig, SharedConfig
from police_thief.domain.enums import Role
from police_thief.domain.state import LocalState
from police_thief.peer.clock import Clock, SystemClock
from police_thief.peer.client import PeerClient
from police_thief.peer.deadline import RetryPolicy, Watchdog
from police_thief.peer.events import EventSink, NullEventSink
from police_thief.peer.gatekeeper import Gatekeeper, GatekeeperLimits
from police_thief.peer.registry import MessageRegistry
from police_thief.peer.states import PeerState, PeerStateMachine
from police_thief.protocol.exceptions import (
    ConflictingDuplicateError,
    InvalidPeerStateError,
    MissingCapabilityError,
    PeerProtocolError,
    WrongGameIdError,
    WrongReceiverRoleError,
    WrongSenderRoleError,
)
from police_thief.protocol.messages import (
    Envelope,
    MessageType,
    new_envelope,
    new_message_id,
)
from police_thief.protocol.versions import (
    MANDATORY_CAPABILITIES,
    PROTOCOL_VERSION,
    SOFTWARE_VERSION,
    SUPPORTED_CAPABILITIES,
)


@dataclass
class HandshakeState:
    """What the opponent has told us, and what we have told them.

    Note what is absent: anything about where the opponent *is*. The handshake
    establishes that both sides loaded the same physics; it conveys no game
    information at all.
    """

    opponent_name: str | None = None
    opponent_software_version: str | None = None
    opponent_capabilities: frozenset[str] = frozenset()
    opponent_config_sha256: str | None = None
    our_hello_acknowledged: bool = False
    our_config_accepted: bool = False
    opponent_ready: bool = False
    we_sent_ready: bool = False

    @property
    def complete(self) -> bool:
        return (
            self.our_hello_acknowledged
            and self.our_config_accepted
            and self.we_sent_ready
            and self.opponent_ready
        )


@dataclass
class PeerOrchestrator:
    """Owns one peer's lifecycle."""

    shared: SharedConfig
    private: PrivateConfig
    game_id: str
    client: PeerClient
    events: EventSink = field(default_factory=NullEventSink)
    clock: Clock = field(default_factory=SystemClock)
    id_factory: Callable[[], str] = new_message_id

    def __post_init__(self) -> None:
        self.role: Role = self.private.role
        self.opponent_role: Role = self.role.opponent
        self.machine = PeerStateMachine(now=self.clock.monotonic)
        self.handshake = HandshakeState()
        self.registry = MessageRegistry(
            capacity=self.shared.rate_limiter_gatekeeper.queue_depth
        )
        self.config_hash = config_sha256(self.shared.raw)
        # This peer's own truth. There is exactly one, for its own role.
        self.state: LocalState = LocalState.initial(self.role, self.shared)
        self.watchdog = Watchdog(
            timeout_sec=self.shared.network_and_league.watchdog_timeout_sec,
            on_stall=self._on_stall,
            clock=self.clock,
        )
        self.failure: str | None = None

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def build_gatekeeper(
        shared: SharedConfig, clock: Clock | None = None
    ) -> Gatekeeper:
        return Gatekeeper(GatekeeperLimits.from_config(shared), clock)

    @staticmethod
    def build_retry_policy(shared: SharedConfig) -> RetryPolicy:
        return RetryPolicy.from_config(shared)

    # ------------------------------------------------------------------
    # Inbound: the server's single callback
    # ------------------------------------------------------------------

    async def handle_message(self, envelope: Envelope) -> Mapping[str, Any]:
        """Handle one validated inbound message.

        Identity is checked before anything else, then duplicates, then state
        legality. Only after all three does the message get acted on.
        """
        self._check_identity(envelope)
        self.watchdog.heartbeat()

        hit = self.registry.lookup(envelope.message_id, envelope.payload)
        if hit is not None:
            self.events.emit(
                "duplicate_suppressed",
                message_id=envelope.message_id,
                message_type=envelope.message_type.value,
            )
            return hit.response

        response = await self._act_on(envelope)
        self.registry.record(envelope.message_id, envelope.payload, response)
        return response

    def _check_identity(self, envelope: Envelope) -> None:
        if envelope.game_id != self.game_id:
            raise WrongGameIdError(
                f"message belongs to game {envelope.game_id!r}, "
                f"this peer is playing {self.game_id!r}"
            )
        if envelope.sender_role is not self.opponent_role:
            raise WrongSenderRoleError(
                f"sender claims role {envelope.sender_role.value!r}; this "
                f"peer's opponent is {self.opponent_role.value!r}"
            )
        if envelope.receiver_role is not self.role:
            raise WrongReceiverRoleError(
                f"message is addressed to {envelope.receiver_role.value!r}, "
                f"this peer is {self.role.value!r}"
            )

    async def _act_on(self, envelope: Envelope) -> Mapping[str, Any]:
        kind = envelope.message_type

        if kind is MessageType.HEALTH_CHECK:
            return _ok(envelope, MessageType.ACK, acknowledged_message_id=envelope.message_id)

        if kind is MessageType.HELLO:
            return self._on_hello(envelope)

        if kind is MessageType.CONFIG_HASH:
            return self._on_config_hash(envelope)

        if kind is MessageType.READY:
            return self._on_ready(envelope)

        if kind in (MessageType.GAME_FINISHED, MessageType.SHUTDOWN):
            self.events.emit(
                "peer_finished",
                message_type=kind.value,
                reason=str(envelope.payload.get("reason", ""))[:200],
            )
            return _ok(
                envelope,
                MessageType.ACK,
                acknowledged_message_id=envelope.message_id,
            )

        if kind is MessageType.ERROR:
            self.events.emit(
                "peer_error",
                code=str(envelope.payload.get("code", ""))[:100],
                detail=str(envelope.payload.get("detail", ""))[:200],
            )
            return _ok(
                envelope,
                MessageType.ACK,
                acknowledged_message_id=envelope.message_id,
            )

        raise InvalidPeerStateError(
            f"message type {kind.value!r} is not accepted in phase 2"
        )

    def _on_hello(self, envelope: Envelope) -> Mapping[str, Any]:
        capabilities = frozenset(envelope.payload["capabilities"])
        missing = MANDATORY_CAPABILITIES - capabilities
        if missing:
            raise MissingCapabilityError(
                f"opponent does not support required capabilities: "
                f"{sorted(missing)}"
            )
        self.handshake.opponent_name = envelope.payload["peer_name"]
        self.handshake.opponent_software_version = envelope.payload[
            "software_version"
        ]
        self.handshake.opponent_capabilities = capabilities
        self.events.emit(
            "hello_received",
            peer_name=self.handshake.opponent_name,
            opponent_software_version=self.handshake.opponent_software_version,
        )
        return _ok(
            envelope,
            MessageType.HELLO,
            peer_name=self.private.game.group_name,
            software_version=SOFTWARE_VERSION,
            capabilities=sorted(SUPPORTED_CAPABILITIES),
        )

    def _on_config_hash(self, envelope: Envelope) -> Mapping[str, Any]:
        theirs = envelope.payload["config_sha256"]
        self.handshake.opponent_config_sha256 = theirs

        if theirs != self.config_hash:
            self.events.emit(
                "config_rejected",
                our_config_sha256=self.config_hash,
                their_config_sha256=theirs,
            )
            return _ok(
                envelope,
                MessageType.CONFIG_REJECTED,
                reason=(
                    "configuration hashes differ; refusing to play because the "
                    "two peers do not share the same physics"
                ),
                our_config_sha256=self.config_hash,
                their_config_sha256=theirs,
            )

        self.events.emit("config_accepted", config_sha256=self.config_hash)
        return _ok(
            envelope, MessageType.CONFIG_ACCEPTED, config_sha256=self.config_hash
        )

    def _on_ready(self, envelope: Envelope) -> Mapping[str, Any]:
        self.handshake.opponent_ready = True
        self.events.emit("peer_ready_received")
        self._maybe_become_ready()
        return _ok(
            envelope,
            MessageType.ACK,
            acknowledged_message_id=envelope.message_id,
        )

    # ------------------------------------------------------------------
    # Outbound: the handshake we drive
    # ------------------------------------------------------------------

    def _envelope(
        self, message_type: MessageType, **payload: Any
    ) -> Envelope:
        return new_envelope(
            game_id=self.game_id,
            sender_role=self.role,
            receiver_role=self.opponent_role,
            message_type=message_type,
            payload=payload,
            message_id=self.id_factory(),
        )

    async def wait_for_peer(self, attempts: int = 30, interval: float = 1.0) -> bool:
        """Poll the opponent's liveness probe until it answers.

        The two processes start independently, so either may be first. Bounded
        by ``attempts`` -- a peer that waits forever for one that never arrives
        is the deadlock Ch. 8 warns about.
        """
        self.machine.transition(PeerState.CONNECTING, "waiting for opponent")
        for attempt in range(1, attempts + 1):
            if await self.client.health_check():
                self.events.emit("peer_reachable", attempts=attempt)
                return True
            await self.clock.sleep(interval)
        self.events.emit("peer_unreachable", attempts=attempts)
        self.machine.transition(PeerState.DISCONNECTED, "opponent never answered")
        self.failure = "peer_unavailable"
        return False

    async def perform_handshake(self) -> bool:
        """Hello, config hash, ready. Returns ``True`` on success."""
        self.machine.transition(PeerState.HELLO_EXCHANGE, "sending hello")
        hello = await self.client.send(
            self._envelope(
                MessageType.HELLO,
                peer_name=self.private.game.group_name,
                software_version=SOFTWARE_VERSION,
                capabilities=sorted(SUPPORTED_CAPABILITIES),
            )
        )
        if not hello.ok or hello.envelope is None:
            return self._fail("hello_rejected", hello.error or "no reply")

        payload = hello.envelope.payload
        capabilities = frozenset(payload.get("capabilities", []))
        missing = MANDATORY_CAPABILITIES - capabilities
        if missing:
            return self._fail(
                "missing_capability", f"opponent lacks {sorted(missing)}"
            )
        self.handshake.opponent_name = payload.get("peer_name")
        self.handshake.opponent_software_version = payload.get("software_version")
        self.handshake.opponent_capabilities = capabilities
        self.handshake.our_hello_acknowledged = True

        self.machine.transition(PeerState.CONFIG_EXCHANGE, "exchanging config hash")
        reply = await self.client.send(
            self._envelope(
                MessageType.CONFIG_HASH,
                config_sha256=self.config_hash,
                config_schema_version=self.shared.schema_version,
            )
        )
        if not reply.ok or reply.envelope is None:
            return self._fail("config_exchange_failed", reply.error or "no reply")

        if reply.envelope.message_type is MessageType.CONFIG_REJECTED:
            self.events.emit(
                "config_mismatch",
                our_config_sha256=self.config_hash,
                their_config_sha256=reply.envelope.payload.get(
                    "our_config_sha256", "?"
                ),
            )
            return self._fail(
                "config_mismatch",
                "the opponent rejected our configuration hash",
            )

        if reply.envelope.message_type is not MessageType.CONFIG_ACCEPTED:
            return self._fail(
                "unexpected_reply",
                f"expected config_accepted, got "
                f"{reply.envelope.message_type.value}",
            )

        theirs = reply.envelope.payload["config_sha256"]
        self.handshake.opponent_config_sha256 = theirs
        if theirs != self.config_hash:
            return self._fail(
                "config_mismatch",
                "the opponent's configuration hash differs from ours",
            )

        self.handshake.our_config_accepted = True
        self.machine.transition(PeerState.CONFIG_VERIFIED, "config hashes match")
        self.events.emit("handshake_ok", config_sha256=self.config_hash)

        self.machine.transition(PeerState.READY_WAIT, "announcing readiness")
        ready = await self.client.send(self._envelope(MessageType.READY))
        if not ready.ok:
            return self._fail("ready_rejected", ready.error or "no reply")
        self.handshake.we_sent_ready = True

        self._maybe_become_ready()
        return True

    async def await_ready(self, attempts: int = 60, interval: float = 0.5) -> bool:
        """Wait for the opponent's READY, which may arrive before or after ours."""
        for _ in range(attempts):
            if self.machine.state is PeerState.READY:
                return True
            if self.machine.is_terminal:
                return False
            await self.clock.sleep(interval)
        return self.machine.state is PeerState.READY

    def _maybe_become_ready(self) -> None:
        if self.handshake.complete and self.machine.state is PeerState.READY_WAIT:
            self.machine.transition(PeerState.READY, "both peers ready")
            self.events.emit("ready", config_sha256=self.config_hash)

    def _fail(self, code: str, detail: str) -> bool:
        self.failure = code
        self.events.emit("handshake_failed", code=code, detail=detail[:200])
        if not self.machine.is_terminal:
            self.machine.transition(PeerState.ERROR, code)
        return False

    def _on_stall(self, silence: float) -> None:
        """Watchdog callback: the peer has gone quiet (E-7).

        Records a structured operational failure and winds down. It does
        **not** decide a game result: the PDF defines a technical loss for a
        side that crashes or exceeds time (Ch. 3, PDF p. 38), but adjudicating
        that is league business, not something a peer declares about itself.
        """
        self.failure = "watchdog_stall"
        self.events.emit("watchdog_stall", silence_seconds=round(silence, 3))
        if not self.machine.is_terminal:
            self.machine.transition(PeerState.DISCONNECTED, "watchdog stall")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def mark_server_ready(self, url: str) -> None:
        self.machine.transition(PeerState.STARTING, "starting server")
        self.machine.transition(PeerState.SERVER_READY, "server listening")
        self.events.emit("server_ready", url=url)

    async def shutdown(self, reason: str = "normal") -> None:
        """Wind down cleanly from wherever we are."""
        await self.watchdog.stop()
        if self.machine.is_terminal:
            self.events.emit("shutdown", reason=reason, state=self.machine.state.value)
            return
        try:
            self.machine.transition(PeerState.FINISHING, reason)
            self.machine.transition(PeerState.FINISHED, reason)
        except InvalidPeerStateError:
            # Already somewhere that cannot reach FINISHING; nothing to undo.
            pass
        self.events.emit("shutdown", reason=reason, state=self.machine.state.value)

    def status(self) -> dict[str, Any]:
        """A summary safe to show a user or a later GUI.

        Contains no opponent position, because there is none to contain.
        """
        return {
            "role": self.role.value,
            "game_id": self.game_id,
            "state": self.machine.state.value,
            "config_sha256": self.config_hash,
            "opponent_name": self.handshake.opponent_name,
            "opponent_ready": self.handshake.opponent_ready,
            "handshake_complete": self.handshake.complete,
            "failure": self.failure,
            "own_position": list(self.state.position.as_tuple()),
        }


def _ok(
    envelope: Envelope, message_type: MessageType, **payload: Any
) -> dict[str, Any]:
    return {
        "ok": True,
        "error": None,
        "envelope": envelope.reply(message_type, payload).to_wire(),
    }
