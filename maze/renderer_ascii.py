"""ASCII renderer with BFS animation, large markers, and Yellow '42' pattern."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Callable

from maze.generator import MazeGenerator
from maze.models import ALL_DIRECTIONS, Cell, Direction
from maze.solver import shortest_path_letters


@dataclass
class RenderTheme:
    """Render theme colors matching the Pygame experience."""

    bg_a: str
    bg_b: str
    wall_color: str
    path_color: str
    search_color: str
    entry_color: str
    exit_color: str
    pattern_42_color: str = "\033[38;2;215;170;35m"  # FILLED_BLOCK (Amarelo)
    reset: str = "\033[0m"


THEMES: list[RenderTheme] = [
    RenderTheme(
        bg_a="\033[48;2;30;30;38m",
        bg_b="\033[48;2;36;36;45m",
        wall_color="\033[38;2;255;255;255m",
        path_color="\033[38;2;0;120;255m",
        search_color="\033[38;2;80;80;80m",
        entry_color="\033[38;2;0;200;0m",
        exit_color="\033[38;2;200;0;0m",
    ),
    RenderTheme(
        bg_a="\033[48;2;12;20;26m",
        bg_b="\033[48;2;20;30;40m",
        wall_color="\033[38;2;120;220;255m",
        path_color="\033[38;2;140;255;170m",
        search_color="\033[38;2;130;205;255m",
        entry_color="\033[38;2;255;210;80m",
        exit_color="\033[38;2;255;120;220m",
    ),
]


def _bfs_visit_order(
    grid: list[list[Cell]],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
) -> list[tuple[int, int]]:
    ex, ey = entry
    tx, ty = exit_
    queue = deque([(ex, ey)])
    visited = {(ex, ey)}
    order = [(ex, ey)]
    while queue:
        x, y = queue.popleft()
        if (x, y) == (tx, ty):
            break
        for direction in ALL_DIRECTIONS:
            if grid[y][x].has_wall(direction):
                continue
            nx, ny = x + direction.dx, y + direction.dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
                order.append((nx, ny))
    return order


def _path_cells_from_letters(
    entry: tuple[int, int], letters: str
) -> list[tuple[int, int]]:
    x, y = entry
    path = [(x, y)]
    for m in letters:
        if m == "N":
            y -= 1
        elif m == "E":
            x += 1
        elif m == "S":
            y += 1
        elif m == "W":
            x -= 1
        path.append((x, y))
    return path


def render_ascii(
    grid: list[list[Cell]],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    search_visited: set[tuple[int, int]] | None = None,
    path_visited: set[tuple[int, int]] | None = None,
    pattern_42_cells: set[tuple[int, int]] | None = None,
    theme_index: int = 0,
) -> str:
    theme = THEMES[theme_index % len(THEMES)]
    search_visited = search_visited or set()
    path_visited = path_visited or set()
    pattern_42_cells = pattern_42_cells or set()
    out_lines = []

    # Borda Superior
    top = f"{theme.wall_color}┏" + "━━━┳" * (width - 1) + "━━━┓" + theme.reset
    out_lines.append(top)

    for y in range(height):
        line_mid = ""
        for x in range(width):
            cell = grid[y][x]
            bg = theme.bg_a if (x + y) % 2 == 0 else theme.bg_b

            # Parede Oeste
            line_mid += (
                f"{theme.wall_color}┃{theme.reset}"
                if cell.has_wall(Direction.WEST)
                else f"{bg} {theme.reset}"
            )

            # Conteúdo (Prioridade: Pattern 42 > Entry/Exit > Path > Search)
            symbol, color = " ", bg
            if (x, y) in pattern_42_cells:
                symbol, color = "█", theme.pattern_42_color
            elif (x, y) == entry:
                symbol, color = "E", theme.entry_color
            elif (x, y) == exit_:
                symbol, color = "X", theme.exit_color
            elif (x, y) in path_visited:
                symbol, color = "█", theme.path_color  # Ponto azul grande
            elif (x, y) in search_visited:
                symbol, color = "▓", theme.search_color  # Ponto cinza denso

            line_mid += f"{bg}{color} {symbol} {theme.reset}"

        line_mid += (
            f"{theme.wall_color}┃{theme.reset}"
            if grid[y][width - 1].has_wall(Direction.EAST)
            else " "
        )
        out_lines.append(line_mid)

        if y < height - 1:
            line_div = f"{theme.wall_color}┣"
            for x in range(width):
                line_div += "━━━" if grid[y][x].has_wall(Direction.SOUTH) else (
                    f"{theme.reset}{theme.bg_a if (x + y) % 2 == 0 else theme.bg_b}"
                    f"   {theme.reset}{theme.wall_color}"
                )
                line_div += "╋" if x < width - 1 else "┫"
            out_lines.append(line_div + theme.reset)

    out_lines.append(
        f"{theme.wall_color}┗" + "━━━┻" * (width - 1) + "━━━┛" + theme.reset
    )
    return "\n".join(out_lines)


def interactive_ascii_session(
    generator_factory: Callable[[], MazeGenerator],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    perfect: bool,
) -> None:
    show_path = True
    theme_idx = 0

    def build_and_animate() -> tuple[
        list[list[Cell]],
        list[tuple[int, int]],
        list[tuple[int, int]],
        set[tuple[int, int]],
    ]:
        gen = generator_factory()
        maze = gen.generate(perfect=perfect)
        path_str = shortest_path_letters(maze.grid, width, height, entry, exit_)
        search_order = _bfs_visit_order(maze.grid, width, height, entry, exit_)
        path_points = _path_cells_from_letters(entry, path_str)
        p42 = maze.pattern_42_cells or set()

        if show_path:
            # Animação de Busca
            for i in range(0, len(search_order), 3):
                print("\033[H", end="")
                print(
                    render_ascii(
                        maze.grid,
                        width,
                        height,
                        entry,
                        exit_,
                        set(search_order[:i]),
                        set(),
                        p42,
                        theme_idx,
                    )
                )
                time.sleep(0.01)

            # Animação do Caminho
            for i in range(len(path_points) + 1):
                print("\033[H", end="")
                print(
                    render_ascii(
                        maze.grid,
                        width,
                        height,
                        entry,
                        exit_,
                        set(search_order),
                        set(path_points[:i]),
                        p42,
                        theme_idx,
                    )
                )
                time.sleep(0.04)

        return maze.grid, search_order, path_points, p42

    grid, search_order, path_points, p42 = build_and_animate()

    while True:
        print("\033[H", end="")
        print(
            render_ascii(
                grid,
                width,
                height,
                entry,
                exit_,
                set(search_order) if show_path else set(),
                set(path_points) if show_path else set(),
                p42,
                theme_idx,
            )
        )
        print(
            f"\n{THEMES[theme_idx % 2].wall_color}R: New | P: Path | C: Color | Q: Quit"
            f"{THEMES[theme_idx % 2].reset}"
        )
        cmd = input("> ").strip().lower()
        if cmd == "q":
            break
        elif cmd == "c":
            theme_idx = (theme_idx + 1) % len(THEMES)
        elif cmd == "p":
            show_path = not show_path
        elif cmd == "r":
            grid, search_order, path_points, p42 = build_and_animate()
