"""A* search for the 8-puzzle with two admissible heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from typing import Callable

State = tuple[int, ...]
GOAL: State = (1, 2, 3, 4, 5, 6, 7, 8, 0)
Heuristic = Callable[[State], int]


@dataclass
class SearchResult:
    path: list[State]
    moves: list[str]
    nodes_expanded: int
    nodes_generated: int


def misplaced_tiles(state: State) -> int:
    """Count numbered tiles not in their goal positions (ignore the blank)."""
    return sum(tile != 0 and tile != GOAL[index] for index, tile in enumerate(state))


def manhattan_distance(state: State) -> int:
    """Sum each numbered tile's row and column distance from its goal."""
    distance = 0
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        current_row, current_col = divmod(index, 3)
        goal_index = tile - 1
        goal_row, goal_col = divmod(goal_index, 3)
        distance += abs(current_row - goal_row) + abs(current_col - goal_col)
    return distance


def manhattan_contributions(state: State) -> list[tuple[int, int, int, int, int, int]]:
    """Return tile, current row/column, goal row/column, and distance."""
    contributions = []
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        row, col = divmod(index, 3)
        goal_index = tile - 1
        goal_row, goal_col = divmod(goal_index, 3)
        distance = abs(row - goal_row) + abs(col - goal_col)
        contributions.append((tile, row, col, goal_row, goal_col, distance))
    return contributions


def inversion_count(state: State) -> int:
    """Count out-of-order numbered tile pairs, excluding the blank."""
    tiles = [tile for tile in state if tile != 0]
    return sum(
        tiles[i] > tiles[j]
        for i in range(len(tiles))
        for j in range(i + 1, len(tiles))
    )


def solvability_rule(state: State) -> tuple[bool, str]:
    """Apply the 3x3 inversion-parity rule and return its explanation."""
    inversions = inversion_count(state)
    solvable = inversions % 2 == 0
    parity = "even" if solvable else "odd"
    reason = (
        f"Rule: ignore the blank and count inverted tile pairs. This board has {inversions} inversions ({parity}); "
        f"a 3x3 8-puzzle is solvable exactly when that count is even."
    )
    return solvable, reason


def is_solvable(state: State) -> bool:
    """For a 3x3 puzzle, a state is solvable iff its inversion count is even."""
    return solvability_rule(state)[0]


def neighbors(state: State) -> list[tuple[State, str]]:
    """Return legal blank moves in a stable order: up, down, left, right."""
    blank = state.index(0)
    row, col = divmod(blank, 3)
    options = []
    if row > 0:
        options.append((blank - 3, "Up"))
    if row < 2:
        options.append((blank + 3, "Down"))
    if col > 0:
        options.append((blank - 1, "Left"))
    if col < 2:
        options.append((blank + 1, "Right"))

    result = []
    for target, move in options:
        next_state = list(state)
        next_state[blank], next_state[target] = next_state[target], next_state[blank]
        result.append((tuple(next_state), move))
    return result


def astar(start: State, heuristic: Heuristic) -> SearchResult:
    """Find an optimal path using A* with f(state) = g(state) + h(state)."""
    if len(start) != 9 or set(start) != set(range(9)):
        raise ValueError("A state must contain each number 0 through 8 exactly once.")
    if not is_solvable(start):
        raise ValueError("This puzzle is unsolvable: its inversion count is odd.")

    serial = count()
    # Tie-break toward lower h, then insertion order, while preserving f priority.
    frontier: list[tuple[int, int, int, int, State]] = []
    start_h = heuristic(start)
    heappush(frontier, (start_h, start_h, 0, next(serial), start))
    came_from: dict[State, tuple[State, str] | None] = {start: None}
    best_g = {start: 0}
    expanded = 0
    generated = 1

    while frontier:
        _, _, queued_g, _, state = heappop(frontier)
        if queued_g != best_g[state]:
            continue  # Ignore an outdated queue entry after finding a shorter route.
        g = queued_g
        if state == GOAL:
            states = [state]
            moves = []
            while came_from[states[-1]] is not None:
                parent, move = came_from[states[-1]]  # type: ignore[misc]
                moves.append(move)
                states.append(parent)
            return SearchResult(list(reversed(states)), list(reversed(moves)), expanded, generated)

        expanded += 1
        for next_state, move in neighbors(state):
            tentative_g = g + 1
            if tentative_g >= best_g.get(next_state, float("inf")):
                continue
            best_g[next_state] = tentative_g
            came_from[next_state] = (state, move)
            h = heuristic(next_state)
            heappush(frontier, (tentative_g + h, h, tentative_g, next(serial), next_state))
            generated += 1

    raise RuntimeError("No solution found, though this state passed the solvability check.")
