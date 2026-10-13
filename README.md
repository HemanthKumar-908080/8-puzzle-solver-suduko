# 8-Puzzle Solver using A*

An educational AI project combining A* search for the 8-puzzle with CSP solvers for 4x4 and 9x9 Sudoku. It compares two admissible A* heuristics and four Sudoku solving strategies.

## Problem formulation

- **State:** the nine tiles in row-major order; `0` represents the blank.
- **Actions:** move the blank one square up, down, left, or right when legal.
- **Goal test:** the state is `1,2,3,4,5,6,7,8,0`.
- **Step cost:** one per move.
- **Evaluation:** A* orders the frontier by `f(n) = g(n) + h(n)`, where `g` is moves so far and `h` estimates remaining moves.

## Heuristics

1. **Misplaced tiles:** count numbered tiles outside their goal positions.
2. **Manhattan distance:** add each numbered tile's horizontal and vertical distance from its goal position.

Both ignore the blank and are admissible: neither can overestimate the number of moves remaining. Manhattan distance is at least as informed as misplaced tiles because every misplaced numbered tile must move at least one square, while Manhattan also counts how far it is from home. A more informed heuristic can reduce the states A* needs to expand, while retaining optimality. The exact counts depend on the input puzzle; compare both on the same input.

## Step-by-step: open and run in VS Code (Windows)

1. Install Python 3.10 or newer from [python.org](https://www.python.org/downloads/). During installation, enable **Add Python to PATH**.
2. Install [Visual Studio Code](https://code.visualstudio.com/) and the **Python** extension published by Microsoft.
3. In VS Code, choose **File → Open Folder…** and select this `8-puzzle-solver` folder.
4. Open **Terminal → New Terminal**. The terminal should start in the project folder. If it does not, change to this folder with `cd`.
5. Check that Python is available:

   ```powershell
   py --version
   ```

6. Start the program:

   ```powershell
   py src/main.py
   ```

7. When prompted, enter the nine tiles row by row. Separate them with spaces or commas, and use `0` for the blank. For example, type:

   ```powershell
   1 2 3 4 0 6 7 5 8
   ```

The program solves the board you enter with both heuristics. It checks that the board is valid and applies the inversion-parity rule before searching. No package installation or `pip install` is needed: the project uses only Python's standard library. If the `py` command is unavailable, try `python` in its place.

The program prints the optimal move sequence and board path for each heuristic, then compares expanded-node counts. It also prints the parity reasoning, per-tile Manhattan contributions, legal successor `g`, `h`, and `f` scores, and a rule-based hint drawn from the optimal solution. A node is counted when it is removed from the priority queue and its legal successors are considered; the goal itself is not counted.

## Run the Sudoku CSP comparison

From the same project terminal, run:

```powershell
py src/main.py --sudoku 4
```

For a 9x9 puzzle, use `py src/main.py --sudoku 9`. Enter each row when prompted, using `0` or `.` for an empty cell. You can enter compact digits (such as `1034` for a 4x4 row) or values separated by spaces. The program solves the same puzzle with plain backtracking, MRV, forward checking, and AC-3, then prints the solution and a comparison table with assignments, backtracks, and runtime. Results depend on the puzzle and computer; the sample in `tests/sudoku_samples.txt` is suitable for demonstrating the 4x4 comparison.

The four methods are cumulative demonstrations: plain backtracking chooses the first empty cell; MRV chooses the empty cell with the fewest legal values; forward checking removes an assigned value from peer domains and detects empty domains early; AC-3 propagates the binary `cell != peer` constraints across arcs before and during search.

## Assignment II extension and CSP/search contrast

The 8-puzzle is modelled as state-space search: each full board is a state, each legal blank move is an action, and A* explores from the initial board toward a goal. Sudoku is modelled as a CSP: each empty cell is a variable, possible digits form its domain, and row, column, and box uniqueness are constraints. See [docs/ia2_extension.md](docs/ia2_extension.md) for the formulations, reasoning rules, comparison method, and report checklist.

## Step-by-step: run in VS Code (macOS/Linux)

1. Install Python 3.10 or newer, Visual Studio Code, and the Microsoft Python extension.
2. Open this project folder in VS Code and choose **Terminal → New Terminal**.
3. Run `python3 --version`, then `python3 src/main.py`.
4. When prompted, enter a board such as `1 2 3 4 0 6 7 5 8`.
5. To provide a board directly, run `python3 src/main.py --state 1,2,3,4,0,6,7,5,8`.
6. To compare Sudoku methods, run `python3 src/main.py --sudoku 4` or `python3 src/main.py --sudoku 9`.

Use `python` instead of `python3` if that is the command on your system.

The program rejects malformed and unsolvable states, prints the optimal move sequence and board path, then reports expanded-node counts for both heuristics on the same user-provided board. A node is counted as expanded when it is removed from the priority queue and its legal successors are considered; the goal itself is not counted.

## Project layout

```text
src/       A* and Sudoku CSP implementations and command-line program
tests/     Sample puzzle inputs for manual checks
docs/      Report drafts and Assignment II formulation
```

## Understanding the comparison

Both runs use the same start state entered by the user, goal, move costs, and A* search. The heuristics only change `h(n)`. Since Manhattan usually gives a larger, more informative lower bound, it is expected to guide the search toward the goal more directly and expand fewer nodes. Its admissibility keeps `f = g + h` from overstating the remaining cost, so A* still finds an optimal solution. Record the actual counts from your run in the report; do not claim Manhattan always expands fewer nodes on every possible input.

## Academic honesty

AI tools may assist, but the assignment requires you to understand and defend the implementation. Cite any substantial external sources you use and write your own explanation of design choices in the report.

## Run the website locally

This project includes a browser interface for the A* 8-puzzle and Sudoku CSP comparison. It uses only Python's standard library and does not need `pip install` or an internet connection.

1. Open the `8-puzzle-solver` folder in VS Code.
2. Choose **Terminal → New Terminal**.
3. Start the local server:

   ```powershell
   py src/web.py
   ```

4. Open `http://127.0.0.1:8000` in your browser.
5. Choose **8-Puzzle** or **Sudoku**. Enter a board, or select **Load sample**, then click the solve button.
6. To stop the local website, return to the VS Code terminal and press **Ctrl+C**.

The server listens only on your own computer. Puzzle inputs stay local and are not sent to an external service.
