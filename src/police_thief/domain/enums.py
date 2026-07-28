"""Enumerations shared across the project.

Values here are structural (they name things), not quantitative. Every
quantitative value comes from configuration -- see config/policy.py.
"""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """The two peer roles.

    The PDF names the sides שוטר (cop/police) and גנב (thief). The reference
    implementation's private-config keys are ``police_class`` and
    ``thief_class`` (Appendix F table 22, PDF p. 159), so ``police`` is the
    canonical spelling for the cop role on the wire and in config.
    """

    POLICE = "police"
    THIEF = "thief"

    @property
    def opponent(self) -> Role:
        return Role.THIEF if self is Role.POLICE else Role.POLICE


class ParameterStatus(str, Enum):
    """The three -- and only three -- statuses used by Appendix F.

    PDF p. 155 states it directly: "the status column in the tables above
    receives one of three values". There is no DEFAULT status and no OPTIONAL
    status; inventing either would be inventing a category.
    """

    FIXED = "fixed"
    """קבוע -- binding, not changeable at all. Deviation disqualifies the team."""

    MINIMUM = "minimum"
    """מינימום -- negotiable only in the direction that makes the game harder;
    never eased below the tabulated value."""

    NEGOTIABLE = "negotiable"
    """משא ומתן -- the sides may agree on any value."""


class AxisOriginCorner(str, Enum):
    """Which corner holds cell (0,0).

    Appendix F table 13 row 3 tabulates ``top-left`` and marks the parameter
    NEGOTIABLE. The PDF names only that one corner; the remaining three are the
    natural completion of "the corner in which cell (0,0) sits" and are accepted
    so a negotiated layout is not rejected out of hand.
    """

    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


class VerbalProvider(str, Enum):
    """How the deception text is produced (Appendix F table 21, PDF p. 158).

    A private per-peer choice, never negotiated. All four modes touch only the
    verbal layer -- the move is always decided in Python.
    """

    TEMPLATE = "template"
    """Zero tokens, offline, the PDF's default."""

    OLLAMA = "ollama"
    CLAUDE_API = "claude_api"
    CLAUDE_CLI = "claude_cli"


class EmailMode(str, Enum):
    """Reporting mode.

    ``send`` is the default and the only mode permitted for a counting league
    match (E-32, E-51; see DECISIONS.md D-5). ``draft`` exists purely as a
    development convenience.
    """

    SEND = "send"
    DRAFT = "draft"
