# A* 8-Puzzle and Sudoku CSP Comparison (working report)

## Problem formulation

The state is a 3 × 3 board represented as nine row-major integers, with 0 as the blank. Legal actions move the blank into an adjacent cell. Each move costs 1. The goal state is `1,2,3 / 4,5,6 / 7,8,0`.

## Approach

The solver uses A*, prioritising states by `f(n) = g(n) + h(n)`. It runs the same start state once with misplaced tiles and once with Manhattan distance. Both heuristics ignore the blank and are admissible lower bounds, so both runs return an optimal solution.

## Initial result

Input: `7,2,4,5,0,6,8,3,1`

| Heuristic | Solution cost | Nodes expanded | Nodes generated |
|---|---:|---:|---:|
| Misplaced tiles | 20 | 2,340 | 3,734 |
| Manhattan distance | 20 | 91 | 155 |

On this fixed input, Manhattan distance expanded 96.1% fewer nodes. Both found a 20-move optimal path. This is an empirical result for the stated input, not a claim that Manhattan must expand fewer nodes on every possible input.

## Why the difference occurs

Every misplaced tile needs at least one move, which gives the misplaced-tiles heuristic a lower bound. Manhattan distance adds the number of horizontal and vertical squares each tile is from home, so it is a tighter lower bound on this puzzle. A* can therefore rule out more states whose estimated total cost is worse, while preserving optimality because the estimate does not overstate the remaining cost.

## Complexity and practical limits

For general A*, runtime and memory are exponential in the solution depth in the worst case; the frontier and explored-state records can consume substantial memory. The 8-puzzle is small enough for this implementation, but harder instances can require much more memory. The node counts above should be regenerated if the code, tie-breaking, or input changes.

## CSP formulation and comparison

Sudoku is modelled with one variable per empty cell, domains containing legal digits, and row, column, and box constraints requiring different values. The program compares plain backtracking, MRV, forward checking, and AC-3 on the same entered puzzle. Include the actual table printed by the program here; do not invent values.

| Variant | Assignments | Backtracks | Runtime (s) |
|---|---:|---:|---:|
| Plain backtracking | Record run | Record run | Record run |
| MRV | Record run | Record run | Record run |
| Forward checking | Record run | Record run | Record run |
| AC-3 | Record run | Record run | Record run |

For this project, the 8-puzzle is formulated as state-space search because the goal is a sequence of blank moves from a start board to a goal board. Sudoku is formulated as a CSP because the goal is a consistent assignment of digits to variables under row, column, and box constraints. Search is useful when actions and paths are central; CSP methods are useful when variables and constraints can prune combinations of values.

## Knowledge, hints, and explainability

For a 3x3 puzzle, the program counts inversions after excluding the blank. Even inversion parity means the board is solvable; odd parity means it is rejected before A*. Demonstrate both an even and an odd input and include the printed rule explanation.

For a solvable board, the program shows each tile's Manhattan contribution along the selected solution and lists legal successor `g`, `h`, and `f` values. Its hint follows the first action of the optimal Manhattan A* path and explains the moved tile and successor scores. Include one explained solution path in the final report.

## Responsible-AI reflection

Explain that the hint exposes its reasoning and is intended for learning. Discuss when state-space search fits a path-finding task and when CSP formulation fits a constraint-filled assignment task. Mention that Sudoku runtime depends on the specific puzzle and hardware, so it is not a universal ranking of solvers.

## Reflection and AI/source note

Working draft: explain the state representation, priority queue, solvability rule, heuristic admissibility, Sudoku variables/domains/constraints, and propagation methods in your own words before submission. Replace all result placeholders with your own program output, add screenshots, and record AI/source assistance honestly. Cite substantial external sources in the final README, as required by the assignment.
