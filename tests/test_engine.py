"""Tests for Hanoi Crossing game engine."""

import pytest

from hanoi_crossing.models import Action, Disk, GameState, Move, Player
from hanoi_crossing.engine import (
    IllegalMoveError,
    apply_move,
    check_win,
    get_legal_moves,
    run_game,
    run_game_random,
    validate_move,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

A = Player.A
B = Player.B


def make_state(n_disks: int = 3) -> GameState:
    return GameState.create(n_disks=n_disks)


def lift(player: Player, pole: str) -> Move:
    return Move(player=player, action=Action.LIFT, pole_id=pole)


def place(player: Player, pole: str) -> Move:
    return Move(player=player, action=Action.PLACE, pole_id=pole)


def skip(player: Player) -> Move:
    return Move(player=player, action=Action.SKIP)


# ---------------------------------------------------------------------------
# Validation — Lift
# ---------------------------------------------------------------------------

class TestValidateLift:
    def test_valid_lift(self):
        state = make_state()
        validate_move(state, lift(A, "1a"))

    def test_lift_hand_full(self):
        state = make_state()
        state.players[A].hand = Disk(size=1, owner=A)
        with pytest.raises(IllegalMoveError, match="hand is not empty"):
            validate_move(state, lift(A, "1a"))

    def test_lift_wrong_pole(self):
        state = make_state()
        with pytest.raises(IllegalMoveError, match="not yours"):
            validate_move(state, lift(A, "1b"))

    def test_lift_empty_pole(self):
        state = make_state()
        with pytest.raises(IllegalMoveError, match="empty"):
            validate_move(state, lift(A, "3a"))

    def test_lift_opponent_disk_from_shared(self):
        state = make_state()
        state.poles["2"].append(Disk(size=2, owner=B))
        validate_move(state, lift(A, "2"))

    def test_lift_opponent_disk_placed_on_own_pole(self):
        state = make_state()
        state.poles["1a"].append(Disk(size=2, owner=B))
        validate_move(state, lift(A, "1a"))


# ---------------------------------------------------------------------------
# Validation — Place
# ---------------------------------------------------------------------------

class TestValidatePlace:
    def test_valid_place_on_empty(self):
        state = make_state()
        state.players[A].hand = Disk(size=1, owner=A)
        validate_move(state, place(A, "3a"))

    def test_place_empty_hand(self):
        state = make_state()
        with pytest.raises(IllegalMoveError, match="hand is empty"):
            validate_move(state, place(A, "3a"))

    def test_place_wrong_pole(self):
        state = make_state()
        state.players[A].hand = Disk(size=1, owner=A)
        with pytest.raises(IllegalMoveError, match="not yours"):
            validate_move(state, place(A, "1b"))

    def test_place_on_smaller_disk(self):
        state = make_state()
        state.poles["3a"] = [Disk(size=1, owner=A)]
        state.players[A].hand = Disk(size=3, owner=A)
        with pytest.raises(IllegalMoveError, match="smaller disk"):
            validate_move(state, place(A, "3a"))

    def test_place_on_larger_disk(self):
        state = make_state()
        state.poles["2"] = [Disk(size=4, owner=B)]
        state.players[A].hand = Disk(size=1, owner=A)
        validate_move(state, place(A, "2"))

    def test_place_opponent_disk_on_own_pole(self):
        state = make_state()
        state.players[A].hand = Disk(size=2, owner=B)
        validate_move(state, place(A, "3a"))

    def test_place_opponent_disk_on_opponent_pole(self):
        state = make_state()
        state.players[A].hand = Disk(size=2, owner=B)
        with pytest.raises(IllegalMoveError, match="not yours"):
            validate_move(state, place(A, "3b"))


# ---------------------------------------------------------------------------
# Validation — Skip
# ---------------------------------------------------------------------------

class TestValidateSkip:
    def test_skip_always_valid(self):
        validate_move(make_state(), skip(A))

    def test_skip_with_disk_in_hand(self):
        state = make_state()
        state.players[A].hand = Disk(size=1, owner=A)
        validate_move(state, skip(A))


# ---------------------------------------------------------------------------
# Apply move
# ---------------------------------------------------------------------------

class TestApplyMove:
    def test_lift(self):
        state = make_state()
        top = state.poles["1a"][-1]
        apply_move(state, lift(A, "1a"))
        assert state.players[A].hand == top
        assert len(state.poles["1a"]) == 2

    def test_place(self):
        state = make_state()
        disk = Disk(size=1, owner=A)
        state.players[A].hand = disk
        apply_move(state, place(A, "3a"))
        assert state.players[A].hand is None
        assert state.poles["3a"][-1] == disk

    def test_skip(self):
        state = make_state()
        poles_before = {k: list(v) for k, v in state.poles.items()}
        apply_move(state, skip(A))
        for k in poles_before:
            assert state.poles[k] == poles_before[k]

    def test_lift_opponent_disk(self):
        state = make_state()
        b_disk = Disk(size=2, owner=B)
        state.poles["2"] = [b_disk]
        apply_move(state, lift(A, "2"))
        assert state.players[A].hand == b_disk

    def test_place_opponent_disk_on_own_pole(self):
        state = make_state()
        b_disk = Disk(size=2, owner=B)
        state.players[A].hand = b_disk
        apply_move(state, place(A, "3a"))
        assert state.poles["3a"][-1] == b_disk


# ---------------------------------------------------------------------------
# Win condition
# ---------------------------------------------------------------------------

class TestCheckWin:
    def test_no_win_initial(self):
        assert not check_win(make_state(), A)

    def test_win_all_visible_poles_clear(self):
        """A wins: hand empty, 1a and 2 empty, disks on 3a."""
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = []
        state.poles["3a"] = [Disk(size=1, owner=A)]
        assert check_win(state, A)

    def test_no_win_disk_in_hand(self):
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = []
        state.players[A].hand = Disk(size=1, owner=A)
        assert not check_win(state, A)

    def test_no_win_disk_on_start_pole(self):
        state = make_state(n_disks=2)
        state.poles["1a"] = [Disk(size=5, owner=A)]
        state.poles["2"] = []
        state.poles["3a"] = [Disk(size=3, owner=A)]
        assert not check_win(state, A)

    def test_no_win_disk_on_shared_pole(self):
        """Any disk on pole 2 blocks A's win."""
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = [Disk(size=2, owner=B)]  # B's disk still visible to A
        state.poles["3a"] = [Disk(size=1, owner=A)]
        assert not check_win(state, A)

    def test_no_win_goal_empty(self):
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = []
        state.poles["3a"] = []
        state.players[A].hand = None
        assert not check_win(state, A)

    def test_win_only_checked_for_given_player(self):
        """B's win state doesn't count for A."""
        state = make_state(n_disks=1)
        state.poles["1b"] = []
        state.poles["2"] = []
        state.poles["3b"] = [Disk(size=2, owner=B)]
        assert not check_win(state, A)  # A hasn't won
        assert check_win(state, B)      # B has won

    def test_win_with_opponent_disks_on_goal(self):
        """A wins with B's disks also on 3a — only visible poles matter."""
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = []
        state.poles["3a"] = [
            Disk(size=2, owner=B),
            Disk(size=1, owner=A),
        ]
        assert check_win(state, A)

    def test_no_win_opponent_disk_on_shared_blocks(self):
        """Even opponent's disk on pole 2 blocks your win."""
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = [Disk(size=4, owner=B)]
        state.poles["3a"] = [Disk(size=1, owner=A)]
        assert not check_win(state, A)


# ---------------------------------------------------------------------------
# Legal moves
# ---------------------------------------------------------------------------

class TestGetLegalMoves:
    def test_initial_state(self):
        moves = get_legal_moves(make_state(), A)
        actions = {m.action for m in moves}
        assert Action.SKIP in actions
        assert Action.LIFT in actions
        assert Action.PLACE not in actions

    def test_with_disk_in_hand(self):
        state = make_state()
        state.players[A].hand = Disk(size=1, owner=A)
        moves = get_legal_moves(state, A)
        actions = {m.action for m in moves}
        assert Action.PLACE in actions
        assert Action.LIFT not in actions

    def test_can_lift_opponent_disk(self):
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = [Disk(size=2, owner=B)]
        moves = get_legal_moves(state, A)
        lift_poles = {m.pole_id for m in moves if m.action == Action.LIFT}
        assert "2" in lift_poles

    def test_place_blocked_by_smaller(self):
        state = make_state()
        state.players[A].hand = Disk(size=5, owner=A)
        state.poles["2"] = [Disk(size=2, owner=B)]
        moves = get_legal_moves(state, A)
        place_poles = {m.pole_id for m in moves if m.action == Action.PLACE}
        assert "2" not in place_poles

    def test_all_moves_have_correct_player(self):
        moves = get_legal_moves(make_state(), A)
        assert all(m.player == A for m in moves)


# ---------------------------------------------------------------------------
# run_game
# ---------------------------------------------------------------------------

class TestRunGame:
    def test_single_disk_win(self):
        moves = [
            lift(A, "1a"),
            skip(B),
            place(A, "3a"),
        ]
        result = run_game(moves, n_disks=1)
        assert result.winner == A
        assert len(result.history) == 3
        assert all(r.valid for r in result.history)

    def test_illegal_move_becomes_skip(self):
        """Illegal moves don't halt the game — they're skipped."""
        moves = [
            place(A, "3a"),  # illegal: empty hand
            lift(B, "1b"),   # B continues normally
        ]
        result = run_game(moves, n_disks=1)
        assert result.winner is None
        assert len(result.history) == 2
        assert not result.history[0].valid
        assert result.history[0].reason != ""
        assert result.history[1].valid

    def test_arbitrary_turn_order(self):
        """Same player can go multiple times in a row."""
        moves = [
            lift(A, "1a"),
            place(A, "3a"),  # A goes twice → wins
        ]
        result = run_game(moves, n_disks=1)
        assert result.winner == A

    def test_draw_on_max_turns(self):
        moves = [skip(A)] * 10
        result = run_game(moves, n_disks=3, max_turns=10)
        assert result.winner is None

    def test_game_stops_after_win(self):
        moves = [
            lift(A, "1a"),
            place(A, "3a"),
            skip(B),          # should not execute
        ]
        result = run_game(moves, n_disks=1)
        assert result.winner == A
        assert len(result.history) == 2


# ---------------------------------------------------------------------------
# run_game_random
# ---------------------------------------------------------------------------

class TestRunGameRandom:
    def test_terminates(self):
        result = run_game_random(n_disks=1, max_turns=500)
        assert result.total_turns <= 500

    def test_all_moves_valid(self):
        result = run_game_random(n_disks=2, max_turns=200)
        assert all(r.valid for r in result.history)

    def test_history_recorded(self):
        result = run_game_random(n_disks=1, max_turns=100)
        assert len(result.history) > 0

    def test_custom_turn_order(self):
        """Can provide custom turn order like A, A, B."""
        result = run_game_random(
            n_disks=1, max_turns=100, turn_order=[A, A, B]
        )
        assert result.total_turns <= 100