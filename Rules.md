# Hanoi Crossing — Rule Specification

## Overview

Two players race to solve their own Tower of Hanoi puzzle. They each have 3 poles, but **share the middle pole**, creating interaction and blocking opportunities. Players alternate turns, one action per turn, until one player wins or the turn limit is reached.

## Board Layout

```
Player A poles: [1a, 2, 3a]
Player B poles: [1b, 2, 3b]
Shared pole:    2
```

- Pole 1a: A start pole
- Pole 3a: A goal pole
- Pole 1b: B start pole
- Pole 3b: B goal pole
- Pole 2: shared by both players

## Disks

- Each player owns **N disks**.
- **Player A** gets disks of **odd** sizes: 1, 3, 5, ..., (2N−1).
- **Player B** gets disks of **even** sizes: 2, 4, 6, ..., 2N.
- Every disk has an **owner** (A or B) and a **size**.

## Initial State

- A's disks are stacked on **pole 1a**, largest on bottom, smallest on top.
- B's disks are stacked on **pole 1b**, largest on bottom, smallest on top.
- Poles 2, 3a, and 3b are empty.
- Both players' hands are **empty**.

## Turn Structure

- Players alternate turns. **Player A goes first.**
- Each turn consists of exactly **one action**: Lift, Place, or Skip.

## Actions

### Lift

Pick up the **top disk** from one of your poles into your hand.

**Legal when:**
- Your hand is empty.
- The target pole belongs to you (1a/2/3a for A, 1b/2/3b for B).
- The target pole is not empty.

**Note:** You may lift **any** top disk, regardless of who owns it. This means you can pick up an opponent's disk from the shared pole or from your own exclusive poles if one was placed there previously.

### Place

Put the disk in your hand onto one of your poles.

**Legal when:**
- Your hand holds a disk.
- The target pole belongs to you.
- The target pole is empty, **OR** the top disk on that pole has size **≥** the held disk's size.

**Note:** You may place the **opponent's disk** onto your own poles. You **cannot** place any disk onto the opponent's exclusive poles.

### Skip

Do nothing. Always legal.

## Pole Ownership

- **Player A** may lift from and place onto poles **1a, 2, 3a**.
- **Player B** may lift from and place onto poles **1b, 2, 3b**.
- A player **cannot interact with the opponent's exclusive poles**.

## Shared Pole (Pole 2) Interactions

- Both players may lift from and place onto pole 2.
- You may lift the top disk regardless of who owns it.
- You may place your disk on top of any disk if the size rule is satisfied.
- Grabbing an opponent's disk from pole 2 and placing it on your own exclusive pole is a valid blocking strategy.

## Win Condition

- A player wins **on their own turn** when, after their action:
  - Their hand is **empty**, AND
  - All N of their disks are on their **goal pole** (3a for A, 3b for B), AND
  - Their disks are in **valid Hanoi order** (largest on bottom, smallest on top).
- **Opponent disks on the goal pole are ignored** for the win check. Only the player's own disks must be present and correctly ordered.
- The win check is performed **only after the active player's action**.

## Termination

- The game ends when a player wins or the **maximum turn limit** is reached.
- The turn limit is a **configurable parameter** (default: 1000 turns).
- If the turn limit is reached with no winner, the game is a **draw**.

## Strategies

### Replay

Reads a pre-recorded sequence of moves and executes them in order. The engine validates each move and outputs the final game state.

### Random Play

Both players select uniformly at random from their set of legal moves each turn. The engine runs until a win or the turn limit.