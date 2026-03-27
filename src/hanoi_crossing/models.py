"""Data models for H-Crossing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Player(Enum):
    A = "A"
    B = "B"

    @property
    def opponent(self) -> Player:
        return Player.B if self == Player.A else Player.A


class Action(Enum):
    LIFT = "LIFT"
    PLACE = "PLACE"
    SKIP = "SKIP"


@dataclass(frozen=True)
class Disk:
    size: int
    owner: Player

    def __str__(self) -> str:
        return f"{self.owner.name}-D{self.size}"


@dataclass
class Move:
    action: Action
    pole_id: str | None = None

    def __str__(self) -> str:
        if self.action == Action.SKIP:
            return "Skip"
        return f"{self.action.value.capitalize()} @ pole {self.pole_id}"


@dataclass
class PlayerState:
    player: Player
    start_pole: str
    goal_pole: str
    poles: list[str]
    hand: Disk | None = None


@dataclass
class MoveRecord:
    """Single entry in the move history log."""

    turn: int
    player: Player
    move: Move
    valid: bool
    reason: str = ""


@dataclass
class GameResult:
    """Returned by the engine after a game completes."""

    final_state: GameState
    history: list[MoveRecord]
    winner: Player | None
    total_turns: int


@dataclass
class GameState:
    n_disks: int
    poles: dict[str, list[Disk]]
    players: dict[Player, PlayerState]
    active_player: Player
    turn: int
    max_turns: int
    winner: Player | None = None

    @classmethod
    def create(cls, n_disks: int, max_turns: int = 1000) -> GameState:
        """Factory method to create the initial game state.

        Disks are stacked largest (bottom) to smallest (top) on each
        player's start pole. All other poles begin empty.
        """
        a_disks = [Disk(size=s, owner=Player.A) for s in range(n_disks, 0, -1)]
        b_disks = [Disk(size=s, owner=Player.B) for s in range(n_disks, 0, -1)]

        poles = {
            "1a": a_disks,
            "2": [],
            "3a": [],
            "1b": b_disks,
            "3b": [],
        }

        players = {
            Player.A: PlayerState(
                player=Player.A,
                start_pole="1a",
                goal_pole="3a",
                poles=["1a", "2", "3a"],
            ),
            Player.B: PlayerState(
                player=Player.B,
                start_pole="1b",
                goal_pole="3b",
                poles=["1b", "2", "3b"],
            ),
        }

        return cls(
            n_disks=n_disks,
            poles=poles,
            players=players,
            active_player=Player.A,
            turn=1,
            max_turns=max_turns,
        )