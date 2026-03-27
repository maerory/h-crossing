"""FastAPI server for Hanoi Crossing."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from hanoi_crossing.engine import IllegalMoveError, run_game, run_game_random
from hanoi_crossing.main import parse_moves
from hanoi_crossing.models import Disk, GameResult, GameState, MoveRecord, Player


# ---------------------------------------------------------------------------
# Pydantic request/response models (separate from game models)
# ---------------------------------------------------------------------------

class ReplayRequest(BaseModel):
    moves: str
    n_disks: int = 3
    max_turns: int = 1000


class RandomRequest(BaseModel):
    n_disks: int = 3
    max_turns: int = 1000


class DiskResponse(BaseModel):
    size: int
    owner: str


class MoveRecordResponse(BaseModel):
    turn: int
    player: str
    action: str
    pole_id: str | None
    valid: bool
    reason: str


class PlayerStateResponse(BaseModel):
    hand: DiskResponse | None
    start_pole: str
    goal_pole: str
    poles: list[str]


class GameStateResponse(BaseModel):
    poles: dict[str, list[DiskResponse]]
    players: dict[str, PlayerStateResponse]
    active_player: str
    turn: int
    n_disks: int


class GameResultResponse(BaseModel):
    winner: str | None
    total_turns: int
    final_state: GameStateResponse
    history: list[MoveRecordResponse]


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def serialize_disk(d: Disk) -> DiskResponse:
    return DiskResponse(size=d.size, owner=d.owner.value)


def serialize_state(state: GameState) -> GameStateResponse:
    return GameStateResponse(
        poles={
            pid: [serialize_disk(d) for d in stack]
            for pid, stack in state.poles.items()
        },
        players={
            p.value: PlayerStateResponse(
                hand=serialize_disk(ps.hand) if ps.hand else None,
                start_pole=ps.start_pole,
                goal_pole=ps.goal_pole,
                poles=ps.poles,
            )
            for p, ps in state.players.items()
        },
        active_player=state.active_player.value,
        turn=state.turn,
        n_disks=state.n_disks,
    )


def serialize_record(r: MoveRecord) -> MoveRecordResponse:
    return MoveRecordResponse(
        turn=r.turn,
        player=r.player.value,
        action=r.move.action.value,
        pole_id=r.move.pole_id,
        valid=r.valid,
        reason=r.reason,
    )


def serialize_result(result: GameResult) -> GameResultResponse:
    return GameResultResponse(
        winner=result.winner.value if result.winner else None,
        total_turns=result.total_turns,
        final_state=serialize_state(result.final_state),
        history=[serialize_record(r) for r in result.history],
    )


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Hanoi Crossing")

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.post("/api/replay", response_model=GameResultResponse)
def api_replay(req: ReplayRequest):
    """Execute a pre-recorded game from move text."""
    try:
        lines = req.moves.strip().splitlines()
        moves = parse_moves(lines)
        result = run_game(moves, n_disks=req.n_disks, max_turns=req.max_turns)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IllegalMoveError as e:
        raise HTTPException(status_code=400, detail=f"Illegal move: {e}")

    return serialize_result(result)


@app.post("/api/random", response_model=GameResultResponse)
def api_random(req: RandomRequest):
    """Run a random game and return the full result."""
    result = run_game_random(n_disks=req.n_disks, max_turns=req.max_turns)
    return serialize_result(result)


# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")