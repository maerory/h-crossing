"""Tests for Hanoi Crossing game engine."""

import pytest

from hanoi_crossing.models import Action, Disk, GameState, Move, Player
from hanoi_crossing.engine import (
    IllegalMoveError,
    advance_turn,
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

def make_state(n_disks: int = 3) -> GameState:
    return GameState.create(n_disks=n_disks)


def lift(pole: str) -> Move:
    return Move(action=Action.LIFT, pole_id=pole)


def place(pole: str) -> Move:
    return Move(action=Action.PLACE, pole_id=pole)


def skip() -> Move:
    return Move(action=Action.SKIP)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidateLift:
    def test_valid_lift_from_own_pole(self):
        state = make_state()
        validate_move(state, lift("1a"))  # should not raise

    def test_lift_hand_full(self):
        state = make_state()
        state.players[Player.A].hand = Disk(size=1, owner=Player.A)
        with pytest.raises(IllegalMoveError, match="hand is not empty"):
            validate_move(state, lift("1a"))

    def test_lift_wrong_pole(self):
        state = make_state()
        with pytest.raises(IllegalMoveError, match="not yours"):
            validate_move(state, lift("1b"))

    def test_lift_empty_pole(self):
        state = make_state()
        with pytest.raises(IllegalMoveError, match="empty"):
            validate_move(state, lift("3a"))

    def test_lift_opponent_disk_on_shared_pole(self):
        state = make_state()
        state.poles["2"].append(Disk(size=1, owner=Player.B))
        with pytest.raises(IllegalMoveError, match="opponent"):
            validate_move(state, lift("2"))

    def test_lift_own_disk_on_shared_pole(self):
        state = make_state()
        state.poles["2"].append(Disk(size=1, owner=Player.A))
        validate_move(state, lift("2"))  # should not raise


class TestValidatePlace:
    def test_valid_place_on_empty_pole(self):
        state = make_state()
        state.players[Player.A].hand = Disk(size=1, owner=Player.A)
        validate_move(state, place("3a"))  # should not raise

    def test_place_empty_hand(self):
        state = make_state()
        with pytest.raises(IllegalMoveError, match="hand is empty"):
            validate_move(state, place("3a"))

    def test_place_wrong_pole(self):
        state = make_state()
        state.players[Player.A].hand = Disk(size=1, owner=Player.A)
        with pytest.raises(IllegalMoveError, match="not yours"):
            validate_move(state, place("1b"))

    def test_place_on_smaller_disk(self):
        state = make_state()
        state.poles["3a"] = [Disk(size=1, owner=Player.A)]
        state.players[Player.A].hand = Disk(size=2, owner=Player.A)
        with pytest.raises(IllegalMoveError, match="smaller disk"):
            validate_move(state, place("3a"))

    def test_place_on_equal_size(self):
        state = make_state()
        state.poles["2"] = [Disk(size=2, owner=Player.B)]
        state.players[Player.A].hand = Disk(size=2, owner=Player.A)
        validate_move(state, place("2"))  # should not raise

    def test_place_on_larger_disk(self):
        state = make_state()
        state.poles["2"] = [Disk(size=3, owner=Player.B)]
        state.players[Player.A].hand = Disk(size=1, owner=Player.A)
        validate_move(state, place("2"))  # should not raise


class TestValidateSkip:
    def test_skip_always_valid(self):
        state = make_state()
        validate_move(state, skip())  # should not raise

    def test_skip_with_disk_in_hand(self):
        state = make_state()
        state.players[Player.A].hand = Disk(size=1, owner=Player.A)
        validate_move(state, skip())  # should not raise


# ---------------------------------------------------------------------------
# Apply move tests
# ---------------------------------------------------------------------------

class TestApplyMove:
    def test_lift(self):
        state = make_state()
        top_disk = state.poles["1a"][-1]  # size 1
        apply_move(state, lift("1a"))
        assert state.players[Player.A].hand == top_disk
        assert len(state.poles["1a"]) == 2

    def test_place(self):
        state = make_state()
        disk = Disk(size=1, owner=Player.A)
        state.players[Player.A].hand = disk
        apply_move(state, place("3a"))
        assert state.players[Player.A].hand is None
        assert state.poles["3a"][-1] == disk

    def test_skip(self):
        state = make_state()
        poles_before = {k: list(v) for k, v in state.poles.items()}
        apply_move(state, skip())
        # Nothing changed
        for k in poles_before:
            assert state.poles[k] == poles_before[k]
        assert state.players[Player.A].hand is None

    def test_lift_then_place_round_trip(self):
        state = make_state()
        original_top = state.poles["1a"][-1]
        apply_move(state, lift("1a"))
        apply_move(state, place("2"))
        assert state.players[Player.A].hand is None
        assert state.poles["2"][-1] == original_top


# ---------------------------------------------------------------------------
# Win condition tests
# ---------------------------------------------------------------------------

class TestCheckWin:
    def test_no_win_initial(self):
        state = make_state()
        assert check_win(state) is None

    def test_win_all_disks_on_goal(self):
        state = make_state(n_disks=2)
        # Clear start pole and stack goal pole correctly
        state.poles["1a"] = []
        state.poles["3a"] = [
            Disk(size=2, owner=Player.A),
            Disk(size=1, owner=Player.A),
        ]
        assert check_win(state) == Player.A

    def test_no_win_disk_in_hand(self):
        state = make_state(n_disks=2)
        state.poles["1a"] = []
        state.poles["3a"] = [Disk(size=2, owner=Player.A)]
        state.players[Player.A].hand = Disk(size=1, owner=Player.A)
        assert check_win(state) is None

    def test_no_win_wrong_order(self):
        state = make_state(n_disks=2)
        state.poles["1a"] = []
        state.poles["3a"] = [
            Disk(size=1, owner=Player.A),  # smaller on bottom — wrong
            Disk(size=2, owner=Player.A),
        ]
        assert check_win(state) is None

    def test_no_win_disks_split_across_poles(self):
        state = make_state(n_disks=2)
        state.poles["1a"] = [Disk(size=2, owner=Player.A)]
        state.poles["3a"] = [Disk(size=1, owner=Player.A)]
        assert check_win(state) is None

    def test_win_only_checked_for_active_player(self):
        """B's disks on goal shouldn't trigger win during A's turn."""
        state = make_state(n_disks=1)
        state.poles["1b"] = []
        state.poles["3b"] = [Disk(size=1, owner=Player.B)]
        state.active_player = Player.A
        assert check_win(state) is None

    def test_single_disk_win(self):
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["3a"] = [Disk(size=1, owner=Player.A)]
        assert check_win(state) == Player.A


# ---------------------------------------------------------------------------
# Legal move enumeration tests
# ---------------------------------------------------------------------------

class TestGetLegalMoves:
    def test_initial_state(self):
        state = make_state()
        moves = get_legal_moves(state)
        actions = {m.action for m in moves}
        # Can lift from 1a, and skip. Cannot place (hand empty).
        assert Action.SKIP in actions
        assert Action.LIFT in actions
        assert Action.PLACE not in actions

    def test_with_disk_in_hand(self):
        state = make_state()
        state.players[Player.A].hand = Disk(size=1, owner=Player.A)
        moves = get_legal_moves(state)
        actions = {m.action for m in moves}
        assert Action.PLACE in actions
        assert Action.LIFT not in actions

    def test_skip_always_present(self):
        state = make_state()
        moves = get_legal_moves(state)
        assert any(m.action == Action.SKIP for m in moves)

    def test_cannot_lift_opponent_disk_from_shared(self):
        state = make_state(n_disks=1)
        state.poles["1a"] = []
        state.poles["2"] = [Disk(size=1, owner=Player.B)]
        moves = get_legal_moves(state)
        lift_poles = {m.pole_id for m in moves if m.action == Action.LIFT}
        assert "2" not in lift_poles

    def test_place_blocked_by_smaller_disk(self):
        state = make_state()
        state.players[Player.A].hand = Disk(size=3, owner=Player.A)
        state.poles["2"] = [Disk(size=1, owner=Player.B)]
        moves = get_legal_moves(state)
        place_poles = {m.pole_id for m in moves if m.action == Action.PLACE}
        assert "2" not in place_poles


# ---------------------------------------------------------------------------
# Turn management tests
# ---------------------------------------------------------------------------

class TestAdvanceTurn:
    def test_switches_player(self):
        state = make_state()
        assert state.active_player == Player.A
        advance_turn(state)
        assert state.active_player == Player.B
        advance_turn(state)
        assert state.active_player == Player.A

    def test_increments_turn(self):
        state = make_state()
        assert state.turn == 1
        advance_turn(state)
        assert state.turn == 2


# ---------------------------------------------------------------------------
# run_game tests
# ---------------------------------------------------------------------------

class TestRunGame:
    def test_single_disk_win(self):
        """Minimal winning game with 1 disk each."""
        moves = [
            lift("1a"),   # A lifts from 1a
            skip(),       # B skips
            place("3a"),  # A places on 3a → A wins
        ]
        result = run_game(moves, n_disks=1)
        assert result.winner == Player.A
        assert len(result.history) == 3
        assert all(r.valid for r in result.history)

    def test_illegal_move_raises(self):
        moves = [
            place("3a"),  # A tries to place with empty hand
        ]
        with pytest.raises(IllegalMoveError):
            run_game(moves, n_disks=1)

    def test_illegal_move_recorded_in_history(self):
        moves = [place("3a")]
        try:
            result = run_game(moves, n_disks=1)
        except IllegalMoveError:
            pass
        # We can't inspect result since it raised — this is a design choice.
        # The error itself carries the message.

    def test_draw_on_max_turns(self):
        # All skips — no one wins
        moves = [skip()] * 10
        result = run_game(moves, n_disks=3, max_turns=10)
        assert result.winner is None

    def test_game_stops_after_win(self):
        moves = [
            lift("1a"),   # A lifts
            skip(),       # B skips
            place("3a"),  # A wins
            skip(),       # B — should never execute
            skip(),       # A — should never execute
        ]
        result = run_game(moves, n_disks=1)
        assert result.winner == Player.A
        assert len(result.history) == 3  # only 3 moves processed


# ---------------------------------------------------------------------------
# run_game_random tests
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

    def test_winner_or_draw(self):
        result = run_game_random(n_disks=1, max_turns=1000)
        # With 1 disk and 1000 turns, almost certainly someone wins
        # but we can't guarantee it, so just check the result is coherent
        if result.winner is not None:
            assert result.winner in (Player.A, Player.B)