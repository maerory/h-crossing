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

Player A moves all disks from **1a → 3a**. Player B moves all disks from **1b → 3b**. First to complete a valid Hanoi stack on their goal pole wins.

### Rules

Players alternate turns starting with Player A. Each turn is exactly one action:

- **Lift** — Pick up the top disk from one of your poles into your hand. You can only lift your own disks.
- **Place** — Put the held disk onto one of your poles. You can place on an empty pole or on top of a disk with equal or greater size, regardless of who owns that disk.
- **Skip** — Do nothing.

Each player can hold at most one disk at a time. A player wins on their own turn when their hand is empty and all N disks are correctly stacked (largest on bottom, smallest on top) on their goal pole.

### The Shared Pole

Pole 2 is where the game gets interesting. Both players can lift from and place onto it, but you can only lift a disk if it belongs to you **and** it's the top disk. This means placing your disk on top of an opponent's disk on the shared pole effectively blocks them from recovering it until you move yours away.

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

Lines starting with `#` and blank lines are ignored.

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

**Replay** — Paste your moves into the text area and click **Run Replay**. The board will animate through each move automatically.

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