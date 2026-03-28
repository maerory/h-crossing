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
    """Raise IllegalMoveError if the move is not legal for the given player."""
    ps = state.players[move.player]

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
    ps = state.players[move.player]

    if move.action == Action.LIFT:
        ps.hand = state.poles[move.pole_id].pop()

    elif move.action == Action.PLACE:
        state.poles[move.pole_id].append(ps.hand)
        ps.hand = None

    # SKIP: no state change


# ---------------------------------------------------------------------------
# Win condition
# ---------------------------------------------------------------------------

def check_win(state: GameState, player: Player) -> bool:
    """Check if the given player has won.

    Win requires: hand is empty, and among the player's visible poles,
    only their goal pole (pole 3) has disks on it. Poles 1 and the
    shared pole must be empty.
    """
    ps = state.players[player]

    if ps.hand is not None:
        return False

    # All visible poles except goal must be empty
    for pole_id in ps.poles:
        if pole_id == ps.goal_pole:
            continue
        if state.poles[pole_id]:
            return False

    # Goal pole must have at least one disk
    if not state.poles[ps.goal_pole]:
        return False

    return True


# ---------------------------------------------------------------------------
# Legal move enumeration
# ---------------------------------------------------------------------------

def get_legal_moves(state: GameState, player: Player) -> list[Move]:
    """Return all legal moves for the given player."""
    moves: list[Move] = [Move(player=player, action=Action.SKIP)]
    ps = state.players[player]

    if ps.hand is None:
        for pole_id in ps.poles:
            stack = state.poles[pole_id]
            if stack:
                moves.append(Move(player=player, action=Action.LIFT, pole_id=pole_id))
    else:
        for pole_id in ps.poles:
            stack = state.poles[pole_id]
            if not stack or stack[-1].size > ps.hand.size:
                moves.append(Move(player=player, action=Action.PLACE, pole_id=pole_id))

    return moves


# ---------------------------------------------------------------------------
# Game loops
# ---------------------------------------------------------------------------

def run_game(moves: list[Move], n_disks: int, max_turns: int = 1000) -> GameResult:
    """Execute a pre-recorded sequence of moves.

    Turn order is determined by the player field on each Move.
    Illegal moves are logged as warnings and treated as skips.
    """
    state = GameState.create(n_disks=n_disks, max_turns=max_turns)
    history: list[MoveRecord] = []

    for i, move in enumerate(moves):
        if state.winner is not None or state.turn > state.max_turns:
            break

        state.active_player = move.player

        try:
            validate_move(state, move)
            apply_move(state, move)
            history.append(
                MoveRecord(
                    turn=state.turn,
                    player=move.player,
                    move=move,
                    valid=True,
                )
            )
        except IllegalMoveError as e:
            # Illegal move → no state change, turn is wasted
            history.append(
                MoveRecord(
                    turn=state.turn,
                    player=move.player,
                    move=move,
                    valid=False,
                    reason=str(e),
                )
            )

        if check_win(state, move.player):
            state.winner = move.player
            break

        state.turn += 1

    return GameResult(
        final_state=state,
        history=history,
        winner=state.winner,
        total_turns=state.turn,
    )


def run_game_random(
    n_disks: int,
    max_turns: int = 1000,
    turn_order: list[Player] | None = None,
) -> GameResult:
    """Run a game with random legal moves.

    If turn_order is provided, it is cycled through. Otherwise defaults
    to alternating A, B, A, B, ...
    """
    state = GameState.create(n_disks=n_disks, max_turns=max_turns)
    history: list[MoveRecord] = []

    if turn_order is None:
        turn_order = [Player.A, Player.B]

    turn_idx = 0

    while state.turn <= state.max_turns and state.winner is None:
        player = turn_order[turn_idx % len(turn_order)]
        state.active_player = player

        legal = get_legal_moves(state, player)
        move = random.choice(legal)

        apply_move(state, move)
        history.append(
            MoveRecord(
                turn=state.turn,
                player=player,
                move=move,
                valid=True,
            )
        )

        if check_win(state, player):
            state.winner = player
            break

        state.turn += 1
        turn_idx += 1

    return GameResult(
        final_state=state,
        history=history,
        winner=state.winner,
        total_turns=state.turn,
    )