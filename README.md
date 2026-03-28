# Hanoi Crossing

A two-player competitive Tower of Hanoi game built in Python. Players race to solve their own puzzle while sharing a middle pole, creating opportunities to block each other.

## The Game

Two players (A and B) each have N disks and three poles. The twist: both players share the center pole.

```
     Player A
┌─────────┐     ┌─────────┐
│ Pole 1a │     │ Pole 3a │
│ (start) │     │  (goal) │
└─────────┘     └─────────┘
          ┌─────────┐
          │ Pole 2  │
          │(shared) │
          └─────────┘
┌─────────┐     ┌─────────┐
│ Pole 1b │     │ Pole 3b │
│ (start) │     │  (goal) │
└─────────┘     └─────────┘
     Player B
```

Player A moves all disks from **1a → 3a**. Player B moves all disks from **1b → 3b**. First to clear all visible poles except their goal pole wins.

### Disks

Player A gets N disks of **odd** sizes (1, 3, 5, ...). Player B gets N disks of **even** sizes (2, 4, 6, ...). All disks across both players are distinct sizes.

### Rules

Turn order is arbitrary — provided externally as a sequence that says which player acts on each step. The engine does not assume alternation. Each turn is exactly one action:

- **Lift** — Pick up the top disk from any of your visible poles into your hand. You can lift any top disk regardless of who owns it.
- **Place** — Put the held disk onto any of your visible poles. You can place on an empty pole or on top of a strictly larger disk. You may place an opponent's disk onto your own poles, but you cannot place any disk onto the opponent's exclusive poles.
- **Skip** — Do nothing.

Each player can hold at most one disk at a time. An illegal action does not change the game state; the turn is wasted and the game continues.

### Visibility

Each player can only see and interact with their own poles:

- **Player A** sees poles 1a, 2, 3a
- **Player B** sees poles 1b, 2, 3b

Neither player can see or interact with the other's exclusive poles. The shared pole (pole 2) is visible to both.

### Win Condition

A player wins when their hand is empty and, among their visible poles, **only their goal pole has disks on it**. This means:

- Their start pole must be empty.
- The shared pole must be completely empty (even opponent disks block your win).
- Their goal pole must have at least one disk.

Opponent disks on your goal pole are fine — only the emptiness of poles 1 and 2 matters. Hanoi ordering on the goal pole is guaranteed by the placement rule.

### The Shared Pole

Pole 2 is where the game gets interesting. Both players can lift from and place onto it. You can grab an opponent's disk from pole 2 and dump it on your own exclusive pole to deny them access. Conversely, any disk left on pole 2 — yours or your opponent's — prevents both players from winning.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd hanoi-crossing
uv sync
```

## CLI Mode

### Replay a recorded game

Create a moves file where each line is `<player> <action> [pole_id]`:

```
# example: 1-disk game, Player A wins
A LIFT 1a
B SKIP
A PLACE 3a
```

Lines starting with `#` and blank lines are ignored. Turn order is determined by the player field on each line — no alternation required.

Run it:

```bash
uv run python -m hanoi_crossing replay <moves-file> -n <disks>
```

Example:

```bash
uv run python -m hanoi_crossing replay replays/1disk_a_wins.txt -n 1
```

### Run a random game

Both players make random legal moves each turn:

```bash
uv run python -m hanoi_crossing random -n <disks> --max-turns <limit>
```

Example:

```bash
uv run python -m hanoi_crossing random -n 3 --max-turns 500
```

### CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `-n`, `--disks` | Number of disks per player | 3 |
| `--max-turns` | Maximum turns before draw | 1000 |

## Web Mode

The web UI provides a visual board with animated disk movement, playback controls, and a move log.

### Start the server

```bash
uv add fastapi uvicorn   # first time only
uv run uvicorn hanoi_crossing.server:app --reload
```

Then open **http://localhost:8000** in your browser.

### Using the web UI

The left sidebar has two tabs:

**Replay** — Paste your moves into the text area and click **Run Replay**. The board will animate through each move automatically. Illegal moves appear crossed out in the move log.

**Random** — Click **Run Random Game** to watch two players make random legal moves.

Both modes support playback controls: pause/resume, speed adjustment via the slider, and reset to replay from the beginning. The move log on the left highlights the current move and color-codes each player's actions.

Configure the number of disks and max turns at the top of the sidebar before running.

## Running Tests

```bash
uv run pytest -v
```

## Project Structure

```
hanoi-crossing/
├── src/hanoi_crossing/
│   ├── models.py      # Data models: Disk, Move, GameState, etc.
│   ├── engine.py      # Validation, state transitions, game loops
│   ├── main.py        # CLI entry point and move parsing
│   └── server.py      # FastAPI server and API routes
├── static/
│   ├── index.html     # Web UI markup
│   ├── style.css      # Styling and board layout
│   └── app.js         # Frontend logic and playback
├── replays/           # Sample replay files
├── tests/             # Pytest test suite
└── pyproject.toml
```