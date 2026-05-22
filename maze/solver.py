from __future__ import annotations

from collections import deque
from maze.models import ALL_DIRECTIONS, Cell


def shortest_path_letters(
    grid: list[list[Cell]],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
) -> str:
    """Compute shortest valid path from entry to exit using BFS.

    Returns:
        String composed of N/E/S/W letters.
    """
    ex, ey = entry
    tx, ty = exit_

    queue: deque[tuple[int, int]] = deque([(ex, ey)])
    visited: set[tuple[int, int]] = {(ex, ey)}
    parent: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}

    while queue:
        x, y = queue.popleft()
        if (x, y) == (tx, ty):
            break

        for direction in ALL_DIRECTIONS:
            if grid[y][x].has_wall(direction):
                continue
            nx = x + direction.dx
            ny = y + direction.dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in visited:
                continue

            visited.add((nx, ny))
            parent[(nx, ny)] = ((x, y), direction.letter)
            queue.append((nx, ny))

    if (tx, ty) not in visited:
        raise RuntimeError("No valid path found between entry and exit.")

    moves: list[str] = []
    current = (tx, ty)
    while current != (ex, ey):
        prev, move = parent[current]
        moves.append(move)
        current = prev

    moves.reverse()
    return "".join(moves)
