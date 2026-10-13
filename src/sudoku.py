"""Sudoku solvers demonstrating four CSP search/propagation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from math import isqrt
from time import perf_counter

Grid = tuple[tuple[int, ...], ...]
Cell = tuple[int, int]


@dataclass
class SudokuResult:
    grid: Grid | None
    assignments: int
    backtracks: int
    runtime_seconds: float


def validate_grid(grid: Grid) -> None:
    size = len(grid)
    box = isqrt(size)
    if size not in (4, 9) or box * box != size:
        raise ValueError("Sudoku must be a 4x4 or 9x9 grid.")
    if any(len(row) != size for row in grid):
        raise ValueError(f"Every row must contain exactly {size} values.")
    if any(value < 0 or value > size for row in grid for value in row):
        raise ValueError(f"Use 0 for an empty cell and values 1 through {size} for clues.")

    for row in range(size):
        values = [value for value in grid[row] if value]
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate clue in row {row + 1}.")
    for col in range(size):
        values = [grid[row][col] for row in range(size) if grid[row][col]]
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate clue in column {col + 1}.")
    for top in range(0, size, box):
        for left in range(0, size, box):
            values = [
                grid[row][col]
                for row in range(top, top + box)
                for col in range(left, left + box)
                if grid[row][col]
            ]
            if len(values) != len(set(values)):
                raise ValueError("Duplicate clue in a sub-grid.")


def peers(cell: Cell, size: int) -> set[Cell]:
    row, col = cell
    box = isqrt(size)
    same_box = {
        (r, c)
        for r in range((row // box) * box, (row // box) * box + box)
        for c in range((col // box) * box, (col // box) * box + box)
    }
    return (
        {(row, c) for c in range(size)}
        | {(r, col) for r in range(size)}
        | same_box
    ) - {cell}


def candidates(grid: list[list[int]], cell: Cell) -> set[int]:
    size = len(grid)
    row, col = cell
    used = set(grid[row])
    used.update(grid[r][col] for r in range(size))
    box = isqrt(size)
    for r in range((row // box) * box, (row // box) * box + box):
        for c in range((col // box) * box, (col // box) * box + box):
            used.add(grid[r][c])
    return set(range(1, size + 1)) - used


def solve_sudoku(puzzle: Grid, method: str) -> SudokuResult:
    """Solve with plain, mrv, forward_checking, or ac3; report search effort."""
    validate_grid(puzzle)
    if method not in {"plain", "mrv", "forward_checking", "ac3"}:
        raise ValueError("Method must be plain, mrv, forward_checking, or ac3.")

    size = len(puzzle)
    grid = [list(row) for row in puzzle]
    assignments = 0
    backtracks = 0
    started = perf_counter()

    if method in {"plain", "mrv"}:
        def search_basic() -> bool:
            nonlocal assignments, backtracks
            empty = [(r, c) for r in range(size) for c in range(size) if grid[r][c] == 0]
            if not empty:
                return True
            if method == "mrv":
                cell = min(empty, key=lambda item: len(candidates(grid, item)))
            else:
                cell = empty[0]
            row, col = cell
            options = sorted(candidates(grid, cell))
            for value in options:
                assignments += 1
                grid[row][col] = value
                if search_basic():
                    return True
                grid[row][col] = 0
            backtracks += 1
            return False

        solved = search_basic()

    elif method == "forward_checking":
        domains = {
            (r, c): candidates(grid, (r, c))
            for r in range(size)
            for c in range(size)
            if grid[r][c] == 0
        }

        def search_forward() -> bool:
            nonlocal assignments, backtracks
            if not domains:
                return True
            cell = min(domains, key=lambda item: (len(domains[item]), item))
            row, col = cell
            selected_domain = set(domains[cell])
            for value in sorted(selected_domain):
                assignments += 1
                changed = {peer: set(domains[peer]) for peer in peers(cell, size) if peer in domains}
                grid[row][col] = value
                del domains[cell]
                failed = False
                for peer in changed:
                    domains[peer].discard(value)
                    if not domains[peer]:
                        failed = True
                if not failed and search_forward():
                    return True
                for peer, old_domain in changed.items():
                    domains[peer] = old_domain
                domains[cell] = selected_domain
                grid[row][col] = 0
            backtracks += 1
            return False

        solved = search_forward()

    else:  # AC-3
        all_cells = [(r, c) for r in range(size) for c in range(size)]
        neighbor_map = {cell: peers(cell, size) for cell in all_cells}
        domains: dict[Cell, set[int]] = {}
        for row in range(size):
            for col in range(size):
                value = grid[row][col]
                domains[(row, col)] = {value} if value else candidates(grid, (row, col))

        def ac3(current: dict[Cell, set[int]], queue: list[tuple[Cell, Cell]]) -> bool:
            if any(not domain for domain in current.values()):
                return False
            while queue:
                left, right = queue.pop()
                revised = {
                    value for value in current[left]
                    if any(value != other for other in current[right])
                }
                if revised != current[left]:
                    current[left] = revised
                    if not revised:
                        return False
                    queue.extend((neighbor, left) for neighbor in neighbor_map[left] if neighbor != right)
            return all(current[cell] for cell in current)

        initial_arcs = [(cell, peer) for cell in all_cells for peer in neighbor_map[cell]]
        solved = ac3(domains, initial_arcs)

        def search_ac3(current: dict[Cell, set[int]]) -> bool:
            nonlocal assignments, backtracks
            unfilled = [cell for cell in all_cells if len(current[cell]) > 1]
            if not unfilled:
                for row, col in all_cells:
                    grid[row][col] = next(iter(current[(row, col)]))
                return True
            cell = min(unfilled, key=lambda item: (len(current[item]), item))
            for value in sorted(current[cell]):
                assignments += 1
                branch = {position: set(domain) for position, domain in current.items()}
                branch[cell] = {value}
                queue = [(peer, cell) for peer in neighbor_map[cell]]
                if ac3(branch, queue) and search_ac3(branch):
                    return True
            backtracks += 1
            return False

        if solved:
            solved = search_ac3(domains)

    elapsed = perf_counter() - started
    result_grid = tuple(tuple(row) for row in grid) if solved else None
    return SudokuResult(result_grid, assignments, backtracks, elapsed)
