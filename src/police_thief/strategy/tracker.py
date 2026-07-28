"""Per-peer tracking of the opponent: belief map plus reconstructed scent.

Holds the two pieces of evidence a peer legally has about its opponent, and
nothing else.

Where the opponent's scent comes from
-------------------------------------
Scent is a function of a trajectory. With no central server, a peer cannot
observe the opponent's field directly -- so it *reconstructs* it from the
opponent's revealed actions, which the commit-reveal protocol already delivers
each turn. Nothing new crosses the wire and the protocol is untouched.

This reconstruction is exact only because the current reveal discloses the
opponent's action precisely. That has a consequence worth stating plainly: a
peer that dead-reckons from the agreed start cell can pin the opponent exactly,
which would make the belief map redundant. The machinery here is therefore built
to carry genuine uncertainty -- diffusion when a move is unknown, scent as a
likelihood, impossible-cell exclusion -- and simply happens to be well-informed
under the present reveal semantics. See OPEN_QUESTIONS.md Q-17, which is a
question for the opponent negotiation, not something to resolve unilaterally.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from police_thief.config.models import SharedConfig
from police_thief.domain.actions import Action, Move, PlaceBarrier
from police_thief.domain.belief import BeliefMap
from police_thief.domain.board import Board
from police_thief.domain.coordinates import Coordinate
from police_thief.domain.enums import Role
from police_thief.domain.scent import ScentField
from police_thief.domain.state import LocalState
from police_thief.strategy.base import LocalView

RECENT_WINDOW = 8
"""How many of our own past cells to remember, for loop avoidance. Long enough
to break an oscillation, short enough that a legitimate return is still open."""


@dataclass
class OpponentTracker:
    """One peer's evidence about the other side."""

    role: Role
    config: SharedConfig
    board: Board
    belief: BeliefMap = field(init=False)
    opponent_scent: ScentField = field(init=False)
    recent_cells: list[Coordinate] = field(default_factory=list)
    _believed_cell: Coordinate | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        opening = self.config.board_and_agents
        start = (
            opening.thief_start if self.role is Role.POLICE else opening.cop_start
        )
        # The opponent's start cell is an agreed, signed condition -- both peers
        # hold it. Seeding from it is reading the shared constitution, not
        # peeking at local truth.
        self._believed_cell = Coordinate.from_pair(start)
        self.belief = BeliefMap.certain(self.board, self._believed_cell)
        self.opponent_scent = ScentField.for_config(self.config, self.board)
        self.opponent_scent.emit(self._believed_cell)

    # ------------------------------------------------------------------

    def note_own_position(self, cell: Coordinate) -> None:
        self.recent_cells.append(cell)
        if len(self.recent_cells) > RECENT_WINDOW:
            self.recent_cells.pop(0)

    def observe_barrier(self, cell: Coordinate) -> None:
        """A declared barrier changes the board for both sides."""
        if not self.board.is_blocked(cell):
            self.board = self.board.with_barrier(cell)
            self.belief.board = self.board
            self.opponent_scent.board = self.board
        self.belief.exclude_impossible()

    def observe_opponent_action(
        self, action: Action, *, own_cell: Coordinate
    ) -> None:
        """Fold a revealed opponent action into belief and scent."""
        direction = action.direction if isinstance(action, Move) else None

        if isinstance(action, PlaceBarrier):
            # The cop forgoes movement to place, so its cell is unchanged.
            self.observe_barrier(action.cell)
            self.belief.predict(None if direction else None)
        else:
            self.belief.predict(direction)

        if self._believed_cell is not None and direction is not None:
            stepped = self._believed_cell.shifted(direction)
            if self.board.is_passable(stepped):
                self._believed_cell = stepped

        if self._believed_cell is not None:
            self.opponent_scent.advance_turn(self._believed_cell)
        else:
            self.opponent_scent.decay()

        self.belief.update_from_scent(self.opponent_scent)
        # Our own cell is one the opponent demonstrably is not on: if it were,
        # the turn would already have ended in a capture.
        self.belief.exclude_impossible(disproven={own_cell})

    # ------------------------------------------------------------------

    def view(self, state: LocalState) -> LocalView:
        """Bundle the legal evidence for the strategy."""
        return LocalView(
            state=state,
            config=self.config,
            belief=self.belief,
            opponent_scent=self.opponent_scent,
            recent_cells=tuple(self.recent_cells),
        )
