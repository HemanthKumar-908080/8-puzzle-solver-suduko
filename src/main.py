"""Run and compare the 8-puzzle A* heuristics."""

import argparse

from solver import (
    GOAL,
    astar,
    manhattan_contributions,
    manhattan_distance,
    misplaced_tiles,
    neighbors,
    solvability_rule,
)
from sudoku import solve_sudoku


SUDOKU_METHODS = (
    ("plain", "Plain backtracking"),
    ("mrv", "Backtracking + MRV"),
    ("forward_checking", "MRV + forward checking"),
    ("ac3", "MRV + AC-3"),
)

def parse_state(text: str) -> tuple[int, ...]:
    try:
        # Accept either comma-separated or space-separated input.
        values = tuple(int(value) for value in text.replace(",", " ").split())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Enter nine numbers from 0 to 8, separated by spaces or commas.") from exc
    if len(values) != 9 or set(values) != set(range(9)):
        raise argparse.ArgumentTypeError("Enter each number 0 through 8 exactly once; use 0 for blank.")
    return values


def print_board(state: tuple[int, ...]) -> None:
    for row in range(0, 9, 3):
        print(" ".join("_" if value == 0 else str(value) for value in state[row : row + 3]))


def show_result(label: str, result) -> None:
    print(f"\n{label}")
    print(f"Solution cost (moves): {len(result.moves)}")
    print(f"Nodes expanded: {result.nodes_expanded}")
    print(f"Nodes generated: {result.nodes_generated}")
    print("Move sequence (blank moves): " + (" -> ".join(result.moves) or "Already solved"))
    print("Solution path:")
    for step, state in enumerate(result.path):
        print(f"\nStep {step}:")
        print_board(state)


def show_manhattan_explanation(path: list[tuple[int, ...]]) -> None:
    print("\nPer-tile Manhattan contributions along the selected solution:")
    for step, state in enumerate(path):
        contributions = manhattan_contributions(state)
        details = "; ".join(
            f"tile {tile}: |{row + 1}-{goal_row + 1}| + |{col + 1}-{goal_col + 1}| = {distance}"
            for tile, row, col, goal_row, goal_col, distance in contributions
        )
        print(f"Step {step}, h={sum(item[-1] for item in contributions)}: {details}")

        if step + 1 < len(path):
            next_state = path[step + 1]
            chosen = next((move for candidate, move in neighbors(state) if candidate == next_state), None)
            moved_tile = state[next_state.index(0)]
            chosen_h = manhattan_distance(next_state)
            chosen_f = step + 1 + chosen_h
            candidates = []
            for candidate, move in neighbors(state):
                tile = state[candidate.index(0)]
                h = manhattan_distance(candidate)
                tag = "chosen optimal-path move" if candidate == next_state else ""
                candidates.append(f"{move} (tile {tile}, g={step + 1}, h={h}, f={step + 1 + h}) {tag}".strip())
            print(
                f"  Hint rule: choose {chosen} (move tile {moved_tile}); it is the next move on the optimal A* path. "
                f"Its score is f=g+h={step + 1}+{chosen_h}={chosen_f}."
            )
            print("  Legal successor scores: " + " | ".join(candidates))


def read_sudoku_grid(size: int) -> tuple[tuple[int, ...], ...]:
    """Prompt for a Sudoku grid; each row accepts digits or separated values."""
    print(f"Enter the {size} Sudoku rows. Use 0 or . for an empty cell.")
    rows = []
    while len(rows) < size:
        raw = input(f"Row {len(rows) + 1}: ").strip()
        tokens = raw.replace(",", " ").split()
        if not any(separator in raw for separator in (" ", ",", "\t")):
            tokens = list(raw)
        try:
            values = tuple(0 if token == "." else int(token) for token in tokens)
        except ValueError:
            print("Enter digits, using 0 or . for blank cells.")
            continue
        if len(values) != size or any(value < 0 or value > size for value in values):
            print(f"This row must contain exactly {size} values from 0 through {size}.")
            continue
        rows.append(values)
    return tuple(rows)


def run_sudoku(size: int) -> None:
    puzzle = read_sudoku_grid(size)
    print("\nInput Sudoku:")
    for row in puzzle:
        print(" ".join("." if value == 0 else str(value) for value in row))

    results = []
    for method, label in SUDOKU_METHODS:
        try:
            result = solve_sudoku(puzzle, method)
        except ValueError as exc:
            print(f"Invalid Sudoku: {exc}")
            return
        results.append((label, result))
        print(f"\n{label}:")
        if result.grid is None:
            print("No solution found.")
        else:
            for row in result.grid:
                print(" ".join(str(value) for value in row))
        print(
            f"Assignments: {result.assignments} | Backtracks: {result.backtracks} | "
            f"Runtime: {result.runtime_seconds:.6f} seconds"
        )

    print("\nSudoku CSP comparison table")
    print(f"{'Variant':30} {'Assignments':>12} {'Backtracks':>12} {'Runtime (s)':>13}")
    for label, result in results:
        print(
            f"{label:30} {result.assignments:12d} {result.backtracks:12d} "
            f"{result.runtime_seconds:13.6f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve an 8-puzzle optimally with A*.")
    parser.add_argument(
        "--sudoku",
        type=int,
        choices=(4, 9),
        metavar="SIZE",
        help="solve a 4x4 or 9x9 Sudoku with four CSP variants",
    )
    parser.add_argument(
        "--state",
        type=parse_state,
        default=None,
        help="optional: nine tiles row by row; use 0 for blank (separate with spaces or commas)",
    )
    args = parser.parse_args()
    if args.sudoku is not None:
        if args.state is not None:
            parser.error("Do not combine --sudoku with --state.")
        run_sudoku(args.sudoku)
        return

    if args.state is None:
        print("Enter the puzzle tiles row by row, using 0 for the blank.")
        print("Example: 1 2 3 4 0 6 7 5 8")
        while True:
            try:
                start = parse_state(input("Puzzle: "))
                break
            except argparse.ArgumentTypeError as exc:
                print(f"Invalid input: {exc}")
    else:
        start = args.state

    solvable, rule_reason = solvability_rule(start)
    print("\nSolvability reasoning:")
    print(rule_reason)
    if not solvable:
        parser.error("The parity rule rejects this input before A* search.")

    print("Start:")
    print_board(start)
    print("\nGoal:")
    print_board(GOAL)

    misplaced = astar(start, misplaced_tiles)
    manhattan = astar(start, manhattan_distance)
    show_result("A* with misplaced-tiles heuristic", misplaced)
    show_result("A* with Manhattan-distance heuristic", manhattan)
    show_manhattan_explanation(manhattan.path)
    if manhattan.nodes_expanded < misplaced.nodes_expanded:
        reduction = 100 * (misplaced.nodes_expanded - manhattan.nodes_expanded) / misplaced.nodes_expanded
        print(f"\nComparison: Manhattan expanded {reduction:.1f}% fewer nodes on this puzzle.")
    elif manhattan.nodes_expanded == misplaced.nodes_expanded:
        print("\nComparison: both heuristics expanded the same number of nodes on this puzzle.")
    else:
        print("\nComparison: this puzzle is an example where Manhattan did not expand fewer nodes.")


if __name__ == "__main__":
    main()
