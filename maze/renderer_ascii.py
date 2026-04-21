"""ASCII renderer with simple interactive controls for maze visualization."""

from __future__ import annotations

from dataclasses import dataclass

from maze.models import Direction
from maze.solver import shortest_path_letters


@dataclass
class RenderTheme:
    """Render theme colors and symbols using ANSI escape codes."""

    wall_color: str
    path_color: str
    entry_color: str
    exit_color: str
    reset: str = "\033[0m"


THEMES: list[RenderTheme] = [
    RenderTheme(
        wall_color="\033[97m",   # white
        path_color="\033[92m",   # green
        entry_color="\033[94m",  # blue
        exit_color="\033[91m",   # red
    ),
    RenderTheme(
        wall_color="\033[96m",   # cyan
        path_color="\033[93m",   # yellow
        entry_color="\033[95m",  # magenta
        exit_color="\033[91m",   # red
    ),
    RenderTheme(
        wall_color="\033[90m",   # gray
        path_color="\033[92m",   # green
        entry_color="\033[93m",  # yellow
        exit_color="\033[95m",   # magenta
    ),
]

MAX_BUILD_ATTEMPTS = 24


def _path_cells_from_letters(
    entry: tuple[int, int],
    letters: str,
) -> set[tuple[int, int]]:
    """Convert NESW path string to visited cell coordinates."""
    x, y = entry
    cells: set[tuple[int, int]] = {(x, y)}
    for move in letters:
        if move == "N":
            y -= 1
        elif move == "E":
            x += 1
        elif move == "S":
            y += 1
        elif move == "W":
            x -= 1
        cells.add((x, y))
    return cells


def render_ascii(
    grid: list[list[object]],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    path_letters: str | None = None,
    show_path: bool = False,
    theme_index: int = 0,
) -> str:
    """Render maze to an ASCII string."""
    theme = THEMES[theme_index % len(THEMES)]
    path_cells: set[tuple[int, int]] = set()

    if show_path and path_letters is not None:
        path_cells = _path_cells_from_letters(entry, path_letters)

    out_lines: list[str] = []

    # Top border
    top = "+"
    for x in range(width):
        cell = grid[0][x]
        north_closed = cell.has_wall(Direction.NORTH)
        top += "---+" if north_closed else "   +"
    out_lines.append(f"{theme.wall_color}{top}{theme.reset}")

    for y in range(height):
        # Middle line (west walls + cell content)
        line_mid = ""
        for x in range(width):
            cell = grid[y][x]
            west_closed = cell.has_wall(Direction.WEST)
            line_mid += f"{theme.wall_color}|{theme.reset}" if west_closed else " "

            symbol = " "
            if (x, y) == entry:
                symbol = f"{theme.entry_color}E{theme.reset}"
            elif (x, y) == exit_:
                symbol = f"{theme.exit_color}X{theme.reset}"
            elif (x, y) in path_cells:
                symbol = f"{theme.path_color}·{theme.reset}"

            line_mid += f" {symbol} "

        # Right border of row
        if grid[y][width - 1].has_wall(Direction.EAST):
            line_mid += f"{theme.wall_color}|{theme.reset}"
        else:
            line_mid += " "
        out_lines.append(line_mid)

        # Bottom line
        line_bot = "+"
        for x in range(width):
            cell = grid[y][x]
            south_closed = cell.has_wall(Direction.SOUTH)
            line_bot += "---+" if south_closed else "   +"
        out_lines.append(f"{theme.wall_color}{line_bot}{theme.reset}")

    return "\n".join(out_lines)


def interactive_ascii_session(
    generator_factory: object,
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    perfect: bool,
) -> None:
    """Run terminal interactive loop for maze visualization.

    generator_factory must be a callable with no args returning a MazeGenerator.
    """
    show_path = True
    theme_index = 0

    def build_once() -> tuple[list[list[object]], str]:
        last_error: RuntimeError | None = None

        for _ in range(MAX_BUILD_ATTEMPTS):
            generator = generator_factory()
            maze = generator.generate(perfect=perfect)
            if not maze.pattern_42_applied:
                print("Warning: '42' pattern could not be applied (maze too small).")
            try:
                path = shortest_path_letters(
                    grid=maze.grid,
                    width=width,
                    height=height,
                    entry=entry,
                    exit_=exit_,
                )
                return maze.grid, path
            except RuntimeError as exc:
                last_error = exc

        if last_error is None:
            raise RuntimeError("Could not generate a valid maze path.")
        raise RuntimeError(
            f"Could not generate a valid maze path after {MAX_BUILD_ATTEMPTS} attempts."
        ) from last_error

    grid, path_letters = build_once()

    while True:
        print("\033[2J\033[H", end="")  # clear screen + cursor home
        print(render_ascii(
            grid=grid,
            width=width,
            height=height,
            entry=entry,
            exit_=exit_,
            path_letters=path_letters,
            show_path=show_path,
            theme_index=theme_index,
        ))
        print("\nCommands: [r] regenerate  [p] toggle path  [c] change colors  [q] quit")
        cmd = input("> ").strip().lower()

        if cmd == "q":
            return
        if cmd == "p":
            show_path = not show_path
        elif cmd == "c":
            theme_index = (theme_index + 1) % len(THEMES)
        elif cmd == "r":
            grid, path_letters = build_once()
