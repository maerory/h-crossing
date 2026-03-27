"""Game engine for Hanoi Crossing - validation, state transitions, and game loops."""

from __future__ import annotations

import random

from hanoi_crossing.models import (
    Action,
    Disk,
    GameResult,
    GameState,
    Move,
    MoveRecord,
    Player,
)


class IllegalMoveError(Exception):
    pass


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_move(state: GameState, move: Move) -> None:
    """Raise IllegalMoveError if the move is not legal for the active player."""
    ps = state.players[state.active_player]

    if move.action == Action.SKIP:
        return

    if move.action == Action.LIFT:
        if ps.hand is not None:
            raise IllegalMoveError("Cannot lift: hand is not empty.")
        if move.pole_id not in ps.poles:
            raise IllegalMoveError(f"Cannot lift: pole {move.pole_id} is not yours.")
        stack = state.poles[move.pole_id]
        if not stack:
            raise IllegalMoveError(f"Cannot lift: pole {move.pole_id} is empty.")
        if stack[-1].owner != ps.player:
            raise IllegalMoveError(
                f"Cannot lift: top disk on pole {move.pole_id} belongs to opponent."
            )
        return

    if move.action == Action.PLACE:
        if ps.hand is None:
            raise IllegalMoveError("Cannot place: hand is empty.")
        if move.pole_id not in ps.poles:
            raise IllegalMoveError(f"Cannot place: pole {move.pole_id} is not yours.")
        stack = state.poles[move.pole_id]
        if stack and stack[-1].size < ps.hand.size:
            raise IllegalMoveError(
                f"Cannot place: disk size {ps.hand.size} onto smaller disk size {stack[-1].size}."
            )
        return


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def apply_move(state: GameState, move: Move) -> None:
    """Apply a validated move, mutating the game state in place."""
    ps = state.players[state.active_player]

    if move.action == Action.LIFT:
        ps.hand = state.poles[move.pole_id].pop()

    elif move.action == Action.PLACE:
        state.poles[move.pole_id].append(ps.hand)
        ps.hand = None

    # SKIP: no state change


# ---------------------------------------------------------------------------
# Win condition
# ---------------------------------------------------------------------------

def check_win(state: GameState) -> Player | None:
    """Check if the active player has won. Returns the winner or None."""
    ps = state.players[state.active_player]

    if ps.hand is not None:
        return None

    goal_stack = state.poles[ps.goal_pole]
    own_disks = [d for d in goal_stack if d.owner == ps.player]

    if len(own_disks) != state.n_disks:
        return None

    # Verify valid Hanoi order: bottom (index 0) is largest, top is smallest
    for i in range(len(own_disks) - 1):
        if own_disks[i].size >= own_disks[i + 1].size:
            pass  # larger or equal below smaller — correct
        else:
            return None

    return ps.player


# ---------------------------------------------------------------------------
# Legal move enumeration
# ---------------------------------------------------------------------------

def get_legal_moves(state: GameState) -> list[Move]:
    """Return all legal moves for the active player."""
    moves: list[Move] = [Move(action=Action.SKIP)]
    ps = state.players[state.active_player]

    if ps.hand is None:
        for pole_id in ps.poles:
            stack = state.poles[pole_id]
            if stack and stack[-1].owner == ps.player:
                moves.append(Move(action=Action.LIFT, pole_id=pole_id))
    else:
        for pole_id in ps.poles:
            stack = state.poles[pole_id]
            if not stack or stack[-1].size >= ps.hand.size:
                moves.append(Move(action=Action.PLACE, pole_id=pole_id))

    return moves


# ---------------------------------------------------------------------------
# Turn management
# ---------------------------------------------------------------------------

def advance_turn(state: GameState) -> None:
    """Switch active player and increment turn counter."""
    state.active_player = state.active_player.opponent
    state.turn += 1


# ---------------------------------------------------------------------------
# Game loops
# ---------------------------------------------------------------------------

def run_game(moves: list[Move], n_disks: int, max_turns: int = 1000) -> GameResult:
    """Execute a pre-recorded sequence of moves.

    Moves alternate between Player A and Player B, starting with A.
    Raises IllegalMoveError if any move is invalid.
    """
    state = GameState.create(n_disks=n_disks, max_turns=max_turns)
    history: list[MoveRecord] = []

    for move in moves:
        if state.winner is not None or state.turn > state.max_turns:
            break

        # Validate — raises on illegal move
        try:
            validate_move(state, move)
        except IllegalMoveError as e:
            history.append(
                MoveRecord(
                    turn=state.turn,
                    player=state.active_player,
                    move=move,
                    valid=False,
                    reason=str(e),
                )
            )
            raise

        apply_move(state, move)
        history.append(
            MoveRecord(
                turn=state.turn,
                player=state.active_player,
                move=move,
                valid=True,
            )
        )

        winner = check_win(state)
        if winner is not None:
            state.winner = winner
            break

        advance_turn(state)

    return GameResult(
        final_state=state,
        history=history,
        winner=state.winner,
        total_turns=state.turn,
    )


def run_game_random(n_disks: int, max_turns: int = 1000) -> GameResult:
    """Both players select uniformly at random from legal moves each turn."""
    state = GameState.create(n_disks=n_disks, max_turns=max_turns)
    history: list[MoveRecord] = []

    while state.turn <= state.max_turns and state.winner is None:
        legal = get_legal_moves(state)
        move = random.choice(legal)

        apply_move(state, move)
        history.append(
            MoveRecord(
                turn=state.turn,
                player=state.active_player,
                move=move,
                valid=True,
            )
        )

        winner = check_win(state)
        if winner is not None:
            state.winner = winner
            break

        advance_turn(state)

    return GameResult(
        final_state=state,
        history=history,
        winner=state.winner,
        total_turns=state.turn,
    )