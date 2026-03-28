## Documenting AI building journey

Model Used:
- Single instance of Claude Opus 4.6

### 2026-03-27 

Dev Time Spent: approx. 1.5 hours

Approach:
- Planned out the project and order of operations:
    - Define the rules & assumptions of the game
    - Design data structures for efficient and coherent code
    - Setting up Python project with uv
    - Implement Model -> Engine -> Main
    - Setting up tests
    - Implement Front-end
- AI involved in each step to maximize efficiency:
    - Hand out instructions at each step, with desired outcome,
    - Review AI code or feedback,
    - Implement, offer my 2 cents,
    - Move onto the next objective.


### 2026-03-28

Dev Time Spent: approx 0.5 hours

Correcting some game rules:
- Each player gets the same 1~N disks -> Player A gets odd disks while Player B gets even disks
- Player can only lift their own disks -> Players can also lift and place their opponent's disk on the visible pole.
- Player needs to have only their disks on the goal pole -> Player can win with their opponents disk on the goal pole as well.
- Player takes alternate turns with Player A going first -> Turn order can be arbitrary.
- Illegal move stops the game -> Illegal move leads to SKIP, the game continues.

Game Assumptions:
- Game is a draw if within all turns, neither player has achieved the win condition.


