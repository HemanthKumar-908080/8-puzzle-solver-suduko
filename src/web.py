from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from solver import (
    astar,
    inversion_count,
    manhattan_contributions,
    manhattan_distance,
    misplaced_tiles,
    neighbors,
    solvability_rule,
)
from sudoku import solve_sudoku

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
HOST = "127.0.0.1"
PORT = 8000
SUDOKU_METHODS = (
    ("plain", "Plain backtracking"),
    ("mrv", "Backtracking + MRV"),
    ("forward_checking", "MRV + forward checking"),
    ("ac3", "MRV + AC-3"),
)


def explain_path(path: list[tuple[int, ...]]) -> list[dict]:
    """Build the per-step Manhattan and successor-score explanation."""
    trace = []
    for step, state in enumerate(path):
        tiles = [
            {
                "tile": tile,
                "row": row + 1,
                "col": col + 1,
                "goal_row": goal_row + 1,
                "goal_col": goal_col + 1,
                "distance": distance,
            }
            for tile, row, col, goal_row, goal_col, distance
            in manhattan_contributions(state)
        ]
        item = {"step": step, "state": list(state), "h": sum(t["distance"] for t in tiles), "tiles": tiles}
        if step + 1 < len(path):
            next_state = path[step + 1]
            chosen_move = next(move for candidate, move in neighbors(state) if candidate == next_state)
            moved_tile = state[next_state.index(0)]
            successors = []
            for candidate, move in neighbors(state):
                tile = state[candidate.index(0)]
                h = manhattan_distance(candidate)
                successors.append({
                    "move": move,
                    "tile": tile,
                    "g": step + 1,
                    "h": h,
                    "f": step + 1 + h,
                    "chosen": candidate == next_state,
                })
            chosen = next(entry for entry in successors if entry["chosen"])
            item["hint"] = {
                "move": chosen_move,
                "tile": moved_tile,
                "g": chosen["g"],
                "h": chosen["h"],
                "f": chosen["f"],
            }
            item["successors"] = successors
        trace.append(item)
    return trace


def solve_puzzle(payload: dict) -> tuple[int, dict]:
    state = payload.get("state")
    if not isinstance(state, list) or len(state) != 9 or any(type(v) is not int for v in state) or set(state) != set(range(9)):
        return 400, {"error": "Enter each tile from 1 to 8 exactly once and leave one cell blank for 0."}

    solvable, reason = solvability_rule(tuple(state))
    if not solvable:
        return 422, {"error": "This board cannot reach the goal.", "solvable": False, "reason": reason, "inversions": inversion_count(tuple(state))}

    misplaced = astar(tuple(state), misplaced_tiles)
    manhattan = astar(tuple(state), manhattan_distance)
    before = misplaced.nodes_expanded
    reduction = round((before - manhattan.nodes_expanded) * 100 / before, 1) if before else 0
    if manhattan.nodes_expanded < before:
        comparison = f"Manhattan expanded {reduction}% fewer nodes on this board."
    elif manhattan.nodes_expanded == before:
        comparison = "Both heuristics expanded the same number of nodes on this board."
    else:
        comparison = "Misplaced tiles expanded fewer nodes on this board; heuristic performance can vary by input."

    return 200, {
        "solvable": True,
        "reason": reason,
        "inversions": inversion_count(tuple(state)),
        "comparison": comparison,
        "reduction_percent": reduction,
        "results": [
            {
                "key": "misplaced",
                "name": "Misplaced tiles",
                "cost": len(misplaced.moves),
                "expanded": misplaced.nodes_expanded,
                "generated": misplaced.nodes_generated,
                "moves": misplaced.moves,
                "path": [list(board) for board in misplaced.path],
            },
            {
                "key": "manhattan",
                "name": "Manhattan distance",
                "cost": len(manhattan.moves),
                "expanded": manhattan.nodes_expanded,
                "generated": manhattan.nodes_generated,
                "moves": manhattan.moves,
                "path": [list(board) for board in manhattan.path],
            },
        ],
        "trace": explain_path(manhattan.path),
    }


def solve_sudoku_request(payload: dict) -> tuple[int, dict]:
    size = payload.get("size")
    grid = payload.get("grid")
    if size not in (4, 9) or not isinstance(grid, list) or len(grid) != size:
        return 400, {"error": "Choose a 4×4 or 9×9 board and enter every row."}
    if any(not isinstance(row, list) or len(row) != size for row in grid):
        return 400, {"error": f"Each row must contain exactly {size} cells."}
    if any(type(value) is not int or value < 0 or value > size for row in grid for value in row):
        return 400, {"error": f"Use values from 1 to {size}; leave empty cells blank."}

    puzzle = tuple(tuple(row) for row in grid)
    results = []
    try:
        for method, label in SUDOKU_METHODS:
            result = solve_sudoku(puzzle, method)
            results.append({
                "key": method,
                "name": label,
                "grid": [list(row) for row in result.grid] if result.grid else None,
                "assignments": result.assignments,
                "backtracks": result.backtracks,
                "runtime_seconds": result.runtime_seconds,
            })
    except ValueError as error:
        return 400, {"error": str(error)}

    solution = next((result["grid"] for result in results if result["grid"] is not None), None)
    return 200, {"size": size, "results": results, "solution": solution}


class SolverHandler(BaseHTTPRequestHandler):
    server_version = "PuzzleLab/1.0"

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8")}
        if route not in files:
            self.send_error(404, "Page not found")
            return
        filename, content_type = files[route]
        data = (WEB_DIR / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        if route not in ("/api/puzzle", "/api/sudoku"):
            self._json(404, {"error": "API route not found."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 100_000:
                self._json(400, {"error": "The request is empty or too large."})
                return
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Expected a JSON object.")
            status, response = solve_puzzle(payload) if route == "/api/puzzle" else solve_sudoku_request(payload)
            self._json(status, response)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            self._json(400, {"error": str(error) or "Invalid request."})

    def _json(self, status: int, data: dict) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, _format: str, *_args) -> None:
        pass


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), SolverHandler)
    print(f"Puzzle Lab is running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the website.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWebsite stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

