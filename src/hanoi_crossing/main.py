
"""Entry point for Hanoi Crossing."""

from __future__ import annotations

import argparse
import sys

from hanoi_crossing.engine import IllegalMoveError, run_game, run_game_random
from hanoi_crossing.models import Action, GameResult, GameState, Move, Player


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def parse_moves(lines: list[str], expected_start: Player = Player.A) -> list[Move]:
    """Parse move lines in the format: <player> <action> [pole_id]
    
    Validation that players alternate correctly starting from expected_start.
    """
    moves: list[Move] = []
    current_player = expected_start

    for i, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if len(parts) < 2 or len(parts) > 3:
            raise ValueError(f"Line {i}: expected '<player> <action> [pole_id]', got '{line}'")
        
        player_str, action_str = parts[0].upper(), parts[1].upper()
        pole_id = parts[2] if len(parts) == 3 else None

        # Validate player
        try:
            player = Player(player_str)
        except ValueError:
            raise ValueError(f"Line {i}: unknown player '{player_str}', expected A or B")
        
        if player != current_player:
            raise ValueError(
                f"Line {i}: expected {current_player.value}'s turn, got {player.value}"
            )
        
        # Validate action
        try:
            action = Action(action_str)
        except ValueError:
            raise ValueError(f"Line {i}: unknown action '{action_str}', expected LIFT/PLACE/SKIP")
        
        # Validate pole_id presence
        if action in (Action.LIFT, Action.PLACE) and pole_id is None:
            raise ValueError(f"Line {i}: {action.value} requires a pole_id")
        if action == Action.SKIP and pole_id is not None:
            raise ValueError(f"Line {i}: SKIP should not have a pole_id")
        
        moves.append(Move(action=action, pole_id=pole_id))
        current_player = current_player.opponent

    return moves


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_state(state: GameState) -> None:
    """Print a human-readable snapshot of the game state."""
    print(f"\n--- Turn {state.turn} | Active: {state.active_player.value} ---")
    for pole_id in ("1a", "2", "3a", "1b", "3b"):
        disks = " ".join(str(d) for d in state.poles[pole_id]) or "(empty)"
        print(f"  Pole {pole_id}: [{disks}]")
    for player in Player:
        hand = state.players[player].hand
        print(f"  {player.value} hand: {hand or '(empty)'}")
    if state.winner:
        print(f"  Winner: {state.winner.value}")
    print()


def print_result(result: GameResult) -> None:
    """Print a summary of the completed game."""
    print("=" * 40)
    if result.winner:
        print(f"Player {result.winner.value} wins on turn {result.total_turns}!")
    else:
        print(f"Draw — turn limit reached ({result.total_turns} turns).")
    print("=" * 40)
    print_state(result.final_state)

    print("Move history:")
    for record in result.history:
        status = "OK" if record.valid else f"ILLEGAL: {record.reason}"
        print(f"  T{record.turn} {record.player.value}: {record.move} [{status}]")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Hanoi Crossing game engine")
    sub = parser.add_subparsers(dest="command", required=True)

    # Replay subcommand
    replay = sub.add_parser("replay", help="Run a pre-recorded game from a file")
    replay.add_argument("file", help="Path to moves file")
    replay.add_argument("-n", "--disks", type=int, default=3, help="Number of disks per player")
    replay.add_argument("--max-turns", type=int, default=1000, help="Maximum turns before draw")

    # Random subcommand
    rand = sub.add_parser("random", help="Run a game with random moves")
    rand.add_argument("-n", "--disks", type=int, default=3, help="Number of disks per player")
    rand.add_argument("--max-turns", type=int, default=1000, help="Maximum turns before draw")

    args = parser.parse_args()

    if args.command == "replay":
        with open(args.file) as f:
            lines = f.readlines()
        moves = parse_moves(lines)
        try:
            result = run_game(moves, n_disks=args.disks, max_turns=args.max_turns)
        except IllegalMoveError as e:
            print(f"Illegal move encountered: {e}", file=sys.stderr)
            sys.exit(1)
        print_result(result)

    elif args.command == "random":
        result = run_game_random(n_disks=args.disks, max_turns=args.max_turns)
        print_result(result)


if __name__ == "__main__":
    main()