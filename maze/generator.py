"""Maze generation algorithms."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from maze.models import ALL_DIRECTIONS, Cell, Direction


@dataclass
class MazeData:
    """Generated maze grid and metadata."""

    width: int
    height: int
    grid: list[list[Cell]]
    pattern_42_applied: bool
    pattern_42_cells: set[tuple[int, int]] = field(default_factory=set)


class MazeGenerator:
    """Generate mazes with reproducibility support via seed."""

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        self.width = width
        self.height = height
        self.seed = seed
        self._rng = random.Random(seed)

    def generate(self, perfect: bool) -> MazeData:
        """Generate a maze according to perfect flag."""
        maze = self._generate_perfect()
        if not perfect:
            self._add_cycles_safely(maze.grid, extra_open_ratio=0.12)

        applied, pattern_cells = self._embed_42_pattern(maze.grid)
        return MazeData(
            width=maze.width,
            height=maze.height,
            grid=maze.grid,
            pattern_42_applied=applied,
            pattern_42_cells=pattern_cells,
        )

    def _generate_perfect(self) -> MazeData:
        """Generate a perfect maze using iterative DFS backtracker."""
        grid = [[Cell() for _ in range(self.width)] for _ in range(self.height)]

        start_x = self._rng.randrange(self.width)
        start_y = self._rng.randrange(self.height)

        stack: list[tuple[int, int]] = [(start_x, start_y)]
        grid[start_y][start_x].visited = True
        visited_count = 1
        total_cells = self.width * self.height

        while stack:
            x, y = stack[-1]
            candidates: list[tuple[Direction, int, int]] = []

            dirs = list(ALL_DIRECTIONS)
            self._rng.shuffle(dirs)

            for direction in dirs:
                nx = x + direction.dx
                ny = y + direction.dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if not grid[ny][nx].visited:
                        candidates.append((direction, nx, ny))

            if not candidates:
                stack.pop()
                continue

            direction, nx, ny = candidates[0]
            self._open_passage(grid, x, y, nx, ny, direction)

            grid[ny][nx].visited = True
            visited_count += 1
            stack.append((nx, ny))

        for row in grid:
            for cell in row:
                cell.visited = False

        if visited_count != total_cells:
            raise RuntimeError("Maze generation failed: not all cells were visited.")

        return MazeData(
            width=self.width,
            height=self.height,
            grid=grid,
            pattern_42_applied=False,
        )

    @staticmethod
    def _open_passage(
        grid: list[list[Cell]],
        x: int,
        y: int,
        nx: int,
        ny: int,
        direction: Direction,
    ) -> None:
        """Open passage consistently between two adjacent cells."""
        grid[y][x].set_wall(direction, closed=False)
        grid[ny][nx].set_wall(direction.opposite, closed=False)

    @staticmethod
    def _close_passage(
        grid: list[list[Cell]],
        x: int,
        y: int,
        nx: int,
        ny: int,
        direction: Direction,
    ) -> None:
        """Close passage consistently between two adjacent cells."""
        grid[y][x].set_wall(direction, closed=True)
        grid[ny][nx].set_wall(direction.opposite, closed=True)

    def _add_cycles_safely(self, grid: list[list[Cell]], extra_open_ratio: float) -> None:
        """Open additional walls to create cycles while avoiding 3x3 open areas."""
        candidates: list[tuple[int, int, Direction]] = []
        for y in range(self.height):
            for x in range(self.width):
                # only east/south to avoid duplicates
                for direction in (Direction.EAST, Direction.SOUTH):
                    nx = x + direction.dx
                    ny = y + direction.dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if grid[y][x].has_wall(direction):
                            candidates.append((x, y, direction))

        self._rng.shuffle(candidates)
        target = int(len(candidates) * extra_open_ratio)
        opened = 0

        for x, y, direction in candidates:
            if opened >= target:
                break

            nx = x + direction.dx
            ny = y + direction.dy

            self._open_passage(grid, x, y, nx, ny, direction)
            if self._creates_open_3x3(grid, x, y):
                self._close_passage(grid, x, y, nx, ny, direction)
                continue

            opened += 1

    def _creates_open_3x3(self, grid: list[list[Cell]], cx: int, cy: int) -> bool:
        """Check local windows for fully open 3x3 areas."""
        min_wx = max(0, cx - 2)
        max_wx = min(self.width - 3, cx)
        min_wy = max(0, cy - 2)
        max_wy = min(self.height - 3, cy)

        for wy in range(min_wy, max_wy + 1):
            for wx in range(min_wx, max_wx + 1):
                if self._window_is_too_open(grid, wx, wy):
                    return True
        return False

    @staticmethod
    def _window_is_too_open(grid: list[list[Cell]], wx: int, wy: int) -> bool:
        """Heuristic: reject 3x3 windows where all internal adjacencies are open."""
        # For a 3x3 block there are 12 internal shared edges.
        open_edges = 0

        # Horizontal edges inside 3x3
        for y in range(wy, wy + 3):
            for x in range(wx, wx + 2):
                if not grid[y][x].has_wall(Direction.EAST):
                    open_edges += 1

        # Vertical edges inside 3x3
        for y in range(wy, wy + 2):
            for x in range(wx, wx + 3):
                if not grid[y][x].has_wall(Direction.SOUTH):
                    open_edges += 1

        return open_edges >= 11  # very open/plaza-like region

    def _embed_42_pattern(self, grid: list[list[Cell]]) -> tuple[bool, set[tuple[int, int]]]:
        """Embed a '42' shape made of fully closed cells if maze is large enough.
        
        Returns:
            Tuple of (applied: bool, pattern_cells: set of (x, y) coordinates).
        """
        pattern = [
            "10010111",
            "10010001",
            "11110111",
            "00010100",
            "00010111",
        ]
        ph = len(pattern)
        pw = len(pattern[0])
        pattern_cells: set[tuple[int, int]] = set()

        if self.width < pw or self.height < ph:
            return False, pattern_cells

        # Place roughly centered
        ox = (self.width - pw) // 2
        oy = (self.height - ph) // 2

        # Apply closed cells where pattern has '1'
        for py in range(ph):
            for px in range(pw):
                if pattern[py][px] == "1":
                    x = ox + px
                    y = oy + py
                    pattern_cells.add((x, y))
                    self._set_fully_closed(grid, x, y)

        return True, pattern_cells

    def _set_fully_closed(self, grid: list[list[Cell]], x: int, y: int) -> None:
        """Turn a cell into fully closed and keep neighbor wall consistency."""
        grid[y][x].walls = 0b1111

        for direction in ALL_DIRECTIONS:
            nx = x + direction.dx
            ny = y + direction.dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                grid[ny][nx].set_wall(direction.opposite, closed=True)