"""Tests for Hanoi Crossing data models."""

from hanoi_crossing.models import Action, Disk, GameState, Move, Player, PlayerState


class TestPlayer:
    def test_opponent(self):
        assert Player.A.opponent == Player.B
        assert Player.B.opponent == Player.A

    def test_values(self):
        assert Player.A.value == "A"
        assert Player.B.value == "B"


class TestDisk:
    def test_creation(self):
        d = Disk(size=3, owner=Player.A)
        assert d.size == 3
        assert d.owner == Player.A

    def test_frozen(self):
        """Disks are immutable."""
        d = Disk(size=1, owner=Player.A)
        try:
            d.size = 2
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass

    def test_str(self):
        assert str(Disk(size=2, owner=Player.B)) == "B-D2"

    def test_equality(self):
        """Frozen dataclasses compare by value."""
        d1 = Disk(size=1, owner=Player.A)
        d2 = Disk(size=1, owner=Player.A)
        d3 = Disk(size=1, owner=Player.B)
        assert d1 == d2
        assert d1 != d3


class TestMove:
    def test_skip_str(self):
        assert str(Move(action=Action.SKIP)) == "Skip"

    def test_lift_str(self):
        assert str(Move(action=Action.LIFT, pole_id="1a")) == "Lift @ pole 1a"

    def test_place_str(self):
        assert str(Move(action=Action.PLACE, pole_id="2")) == "Place @ pole 2"


class TestGameStateCreate:
    def test_initial_poles(self):
        state = GameState.create(n_disks=3)
        # P1 start pole: 3 disks, largest on bottom
        assert len(state.poles["1a"]) == 3
        assert state.poles["1a"][0].size == 3  # bottom
        assert state.poles["1a"][-1].size == 1  # top
        # P2 start pole
        assert len(state.poles["1b"]) == 3
        assert state.poles["1b"][0].size == 3
        assert state.poles["1b"][-1].size == 1
        # All other poles empty
        assert state.poles["2"] == []
        assert state.poles["3a"] == []
        assert state.poles["3b"] == []

    def test_initial_disk_ownership(self):
        state = GameState.create(n_disks=2)
        for d in state.poles["1a"]:
            assert d.owner == Player.A
        for d in state.poles["1b"]:
            assert d.owner == Player.B

    def test_initial_hands_empty(self):
        state = GameState.create(n_disks=3)
        assert state.players[Player.A].hand is None
        assert state.players[Player.B].hand is None

    def test_initial_active_player(self):
        state = GameState.create(n_disks=3)
        assert state.active_player == Player.A

    def test_initial_turn(self):
        state = GameState.create(n_disks=3)
        assert state.turn == 1
        assert state.winner is None

    def test_n_disks_stored(self):
        state = GameState.create(n_disks=5)
        assert state.n_disks == 5

    def test_player_poles(self):
        state = GameState.create(n_disks=3)
        assert state.players[Player.A].poles == ["1a", "2", "3a"]
        assert state.players[Player.B].poles == ["1b", "2", "3b"]

    def test_player_goals(self):
        state = GameState.create(n_disks=3)
        assert state.players[Player.A].start_pole == "1a"
        assert state.players[Player.A].goal_pole == "3a"
        assert state.players[Player.B].start_pole == "1b"
        assert state.players[Player.B].goal_pole == "3b"

    def test_custom_max_turns(self):
        state = GameState.create(n_disks=3, max_turns=500)
        assert state.max_turns == 500

    def test_single_disk(self):
        state = GameState.create(n_disks=1)
        assert len(state.poles["1a"]) == 1
        assert state.poles["1a"][0] == Disk(size=1, owner=Player.A)