# Assignment II extension: CSP, reasoning, and explainability

This document describes the extension implemented in the project. Run the program on your own inputs and copy the measured results into the final report; runtime and search counts depend on the puzzle and computer.

## CSP formulation: Sudoku

The solver accepts 4x4 and 9x9 Sudoku boards. For a board of size `N`:

- **Variables:** one variable for each empty cell.
- **Domains:** values `1..N` that do not already occur in that cell's row, column, or square box.
- **Constraints:** any two cells sharing a row, column, or box must have different values.
- **Goal:** assign every variable while satisfying every constraint.

Four strategies solve the same entered board:

1. **Plain backtracking:** choose the first empty cell in row-major order and try legal values.
2. **MRV:** choose the empty cell with the fewest legal values, then backtrack on conflict.
3. **Forward checking:** after an assignment, remove its value from unassigned peer domains and backtrack immediately if a domain becomes empty.
4. **AC-3:** enforce arc consistency for the binary `cell != peer` constraints initially and after each tentative assignment, then use MRV to branch.

The program reports **assignments** as the number of tentative value placements, **backtracks** as failed recursive search levels, and **runtime** as wall-clock seconds measured with Python's monotonic performance timer. The exact runtime is machine-dependent; compare variants on the same puzzle and environment.

### Results table to include in the report

Run `py src/main.py --sudoku 4` and/or `py src/main.py --sudoku 9`. Copy the table printed by the program into the report and state which sample/input was used.

| Variant | Assignments | Backtracks | Runtime (s) |
|---|---:|---:|---:|
| Plain backtracking | Fill from run | Fill from run | Fill from run |
| MRV | Fill from run | Fill from run | Fill from run |
| Forward checking | Fill from run | Fill from run | Fill from run |
| AC-3 | Fill from run | Fill from run | Fill from run |

## How the 8-puzzle differs from a CSP

The 8-puzzle is a **state-space search** problem. A state is the complete board; actions move the blank; the goal is a particular board; and each move has a cost. A* explores reachable states and uses `g+h` to order them.

Sudoku is a **constraint satisfaction** problem. Its variables are individual blank cells, domains are candidate digits, and constraints describe which assignments may coexist. CSP solvers choose variables and propagate constraints instead of searching for a sequence of board-moving actions.

Search is a natural fit when the task asks for a path or action sequence, such as solving the 8-puzzle. CSP methods are a natural fit when many variable values must jointly satisfy constraints, such as filling Sudoku. Either formulation can sometimes model other tasks, but the clearest formulation depends on what counts as a solution and what structure can prune choices.

## Knowledge and reasoning for the 8-puzzle

### Inversion-parity rule

The program counts inversions in the row-major sequence after excluding the blank. An inversion is a pair of numbered tiles that appear in the opposite order from their goal order. For a 3x3 8-puzzle:

```text
IF inversion_count is even THEN the board is solvable.
IF inversion_count is odd THEN reject the board before A* search.
```

The program prints the inversion count and the rule outcome before starting either heuristic search. `tests/sample_states.txt` includes an odd-parity board to use for the rejection demonstration.

### Rule-based next-move hint

For a valid, solvable board, the program finds an optimal route with A* and provides an explanation of the next action:

```text
IF the board is the goal THEN report that no move is needed.
ELSE recommend the first blank move on the Manhattan A* optimal path.
Explain the moved tile, its Manhattan contribution, and the successor's g, h, and f scores.
```

For each state along the selected route, the output lists every numbered tile's current and goal row/column and its Manhattan contribution. It also lists legal successor scores and marks the move on the optimal route. This makes clear that a shortest-path move is selected using the complete A* search, rather than a greedy rule that only looks one step ahead.

## Applied and responsible AI

The solver shows the rule and search evidence behind a recommendation so a student can inspect it. The hint is educational guidance: it does not hide the search process or claim that a lower heuristic score by itself proves an action is correct. Reported Sudoku timings are local measurements and should not be treated as a universal ranking across all boards or computers.

## Demonstration checklist

- Run both 4x4 and 9x9 Sudoku variants; include the comparison table for the chosen input.
- Show a valid even-parity 8-puzzle and an odd-parity input rejected before search.
- Show one solved 8-puzzle path with its per-tile Manhattan contributions and next-move explanation.
- Explain why the 8-puzzle is naturally described as state-space search and Sudoku as a CSP.
- Record the puzzle inputs, actual output counts, and any AI/source assistance honestly in the report.
