"""Graphical renderer (equivalent to MLX-style requirements) using pygame."""

from __future__ import annotations

from collections import deque
from typing import Callable, TypedDict

import pygame

from maze.generator import MazeGenerator
from maze.models import ALL_DIRECTIONS, Cell, Direction
from maze.solver import shortest_path_letters
from maze.writer import write_maze_file

CELL_SIZE = 36
WALL_THICKNESS = 2
PADDING = 20
FPS = 60
CELL_RADIUS = 6
PATH_INSET = CELL_SIZE // 4
MARKER_INSET = CELL_SIZE // 6
OPEN_CELL_A = (30, 30, 38)
OPEN_CELL_B = (36, 36, 45)
FILLED_BLOCK = (215, 170, 35)
FILLED_BLOCK_BORDER = (245, 218, 120)
MAX_BUILD_ATTEMPTS = 24
SEARCH_STEPS_PER_FRAME = 2
PATH_STEPS_PER_FRAME = 1


Color3 = tuple[int, int, int]
Color4 = tuple[int, int, int, int]


class Theme(TypedDict):
    """Pygame color palette for the renderer."""

    bg: Color3
    cell_wall: Color3
    entry: Color3
    exit: Color3
    path: Color3
    path_glow: Color4
    search: Color3
    search_glow: Color4
    text: Color3
    warning: Color3


THEMES: list[Theme] = [
    {
        "bg": (20, 20, 20),
        "cell_wall": (255, 255, 255),
        "entry": (0, 200, 0),
        "exit": (200, 0, 0),
        "path": (0, 120, 255),
        "path_glow": (0, 120, 255, 0),
        "search": (120, 120, 120),
        "search_glow": (120, 120, 120, 0),
        "text": (255, 255, 255),
        "warning": (255, 200, 0),
    },
    {
        "bg": (12, 20, 26),
        "cell_wall": (120, 220, 255),
        "entry": (255, 210, 80),
        "exit": (255, 120, 220),
        "path": (140, 255, 170),
        "path_glow": (140, 255, 170, 52),
        "search": (130, 205, 255),
        "search_glow": (130, 205, 255, 36),
        "text": (220, 240, 255),
        "warning": (255, 235, 140),
    },
]


def _mix_color(
    first: Color3,
    second: Color3,
    ratio: float,
) -> Color3:
    red = int(round(first[0] * (1 - ratio) + second[0] * ratio))
    green = int(round(first[1] * (1 - ratio) + second[1] * ratio))
    blue = int(round(first[2] * (1 - ratio) + second[2] * ratio))
    return (red, green, blue)


def _draw_cell_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    cell: Cell,
    theme: Theme,
    x: int,
    y: int,
    is_pattern_42: bool = False,
) -> None:
    inset = rect.inflate(-2, -2)
    if is_pattern_42:
        pygame.draw.rect(surface, FILLED_BLOCK, inset, border_radius=CELL_RADIUS)
        pygame.draw.rect(
            surface, FILLED_BLOCK_BORDER, inset, width=2, border_radius=CELL_RADIUS
        )
        return

    base = OPEN_CELL_A if (x + y) % 2 == 0 else OPEN_CELL_B
    rim = _mix_color(base, theme["bg"], 0.22)
    pygame.draw.rect(surface, base, inset, border_radius=CELL_RADIUS)
    pygame.draw.rect(surface, rim, inset, width=1, border_radius=CELL_RADIUS)


def _draw_path_overlay(
    surface: pygame.Surface,
    path_points: list[tuple[int, int]],
    ox: int,
    oy: int,
    theme: Theme,
) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    for gx, gy in path_points:
        cell_rect = pygame.Rect(
            ox + gx * CELL_SIZE,
            oy + gy * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        tile_rect = cell_rect.inflate(-PATH_INSET, -PATH_INSET)
        path_fill = tuple(theme["path"]) + (210,)
        pygame.draw.rect(overlay, path_fill, tile_rect, border_radius=CELL_RADIUS)

    surface.blit(overlay, (0, 0))


def _draw_search_overlay(
    surface: pygame.Surface,
    search_points: list[tuple[int, int]],
    ox: int,
    oy: int,
    theme: Theme,
) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

    for gx, gy in search_points:
        cell_rect = pygame.Rect(
            ox + gx * CELL_SIZE,
            oy + gy * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
        )
        tile_rect = cell_rect.inflate(-(PATH_INSET + 2), -(PATH_INSET + 2))
        if tile_rect.width <= 0 or tile_rect.height <= 0:
            continue
        search_fill = tuple(theme["search"]) + (180,)
        pygame.draw.rect(
            overlay, search_fill, tile_rect, border_radius=max(4, CELL_RADIUS - 2)
        )

    surface.blit(overlay, (0, 0))


def _draw_marker(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: Color3,
) -> None:
    shadow = rect.inflate(4, 4)
    pygame.draw.rect(surface, (0, 0, 0), shadow, border_radius=CELL_RADIUS)
    pygame.draw.rect(surface, color, rect, border_radius=CELL_RADIUS)
    outline = _mix_color(color, (255, 255, 255), 0.18)
    pygame.draw.rect(surface, outline, rect, width=2, border_radius=CELL_RADIUS)


def _path_points(entry: tuple[int, int], moves: str) -> list[tuple[int, int]]:
    x, y = entry
    points = [(x, y)]
    for m in moves:
        if m == "N":
            y -= 1
        elif m == "E":
            x += 1
        elif m == "S":
            y += 1
        elif m == "W":
            x -= 1
        points.append((x, y))
    return points


def _bfs_visit_order(
    grid: list[list[Cell]],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
) -> list[tuple[int, int]]:
    ex, ey = entry
    tx, ty = exit_

    queue: deque[tuple[int, int]] = deque([(ex, ey)])
    visited: set[tuple[int, int]] = {(ex, ey)}
    order: list[tuple[int, int]] = [(ex, ey)]

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
            queue.append((nx, ny))
            order.append((nx, ny))

    return order


def run_gui_session(
    generator_factory: Callable[[], MazeGenerator],
    width: int,
    height: int,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    perfect: bool,
    output_file: str | None = None,
) -> None:
    pygame.init()
    pygame.display.set_caption("A-Maze-ing (GUI)")

    maze_w = width * CELL_SIZE
    maze_h = height * CELL_SIZE
    info_h = 96
    screen = pygame.display.set_mode(
        (maze_w + 2 * PADDING, maze_h + 2 * PADDING + info_h)
    )
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 20)
    status_font = pygame.font.SysFont("monospace", 16)

    show_path = True
    theme_idx = 0
    status_message = ""
    search_points: list[tuple[int, int]] = []
    path_points: list[tuple[int, int]] = []
    search_progress = 0
    path_progress = 0
    animation_phase = "done"
    pattern_42_cells: set[tuple[int, int]] = set()

    def restart_animation(
        new_search_points: list[tuple[int, int]],
        new_path_points: list[tuple[int, int]],
    ) -> None:
        nonlocal search_points, path_points, search_progress, path_progress, animation_phase
        search_points = new_search_points
        path_points = new_path_points
        search_progress = 0
        path_progress = 0
        animation_phase = "search"

    def build_once() -> (
        tuple[list[list[Cell]], str, list[tuple[int, int]], str, set[tuple[int, int]]]
    ):
        last_error: RuntimeError | None = None
        for _ in range(MAX_BUILD_ATTEMPTS):
            gen = generator_factory()
            maze = gen.generate(perfect=perfect)
            local_status = ""
            if not maze.pattern_42_applied:
                local_status = "42 nao pode ser exibido no centro (labirinto pequeno)."
                print(f"Warning: {local_status}")
            try:
                path = shortest_path_letters(maze.grid, width, height, entry, exit_)
                search_order = _bfs_visit_order(maze.grid, width, height, entry, exit_)
                return (
                    maze.grid,
                    path,
                    search_order,
                    local_status,
                    maze.pattern_42_cells or set(),
                )
            except RuntimeError as exc:
                # The centered '42' mask can occasionally disconnect entry and exit.
                last_error = exc

        if last_error is None:
            raise RuntimeError("Could not generate a valid maze path.")
        raise RuntimeError(
            f"Could not generate a valid maze path after {MAX_BUILD_ATTEMPTS} attempts."
        ) from last_error

    def persist_current_maze(current_grid: list[list[Cell]], current_path: str) -> None:
        nonlocal status_message
        if output_file is None:
            return
        try:
            write_maze_file(
                output_file=output_file,
                grid=current_grid,
                entry=entry,
                exit_=exit_,
                path_letters=current_path,
            )
        except OSError as exc:
            io_status = f"Falha ao salvar output: {exc}"
            print(f"Warning: {io_status}")
            if status_message:
                status_message = f"{status_message} | {io_status}"
            else:
                status_message = io_status

    grid, path_moves, initial_search_order, status_message, pattern_42_cells = (
        build_once()
    )
    persist_current_maze(grid, path_moves)
    restart_animation(initial_search_order, _path_points(entry, path_moves))

    running = True
    while running:
        clock.tick(FPS)
        theme = THEMES[theme_idx % len(THEMES)]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    try:
                        (
                            grid,
                            path_moves,
                            search_order,
                            status_message,
                            pattern_42_cells,
                        ) = build_once()
                        persist_current_maze(grid, path_moves)
                        restart_animation(search_order, _path_points(entry, path_moves))
                    except RuntimeError as exc:
                        print(f"Warning: {exc}")
                        status_message = str(exc)
                elif event.key == pygame.K_p:
                    show_path = not show_path
                elif event.key == pygame.K_c:
                    theme_idx = (theme_idx + 1) % len(THEMES)

        if show_path:
            if animation_phase == "search":
                search_progress = min(
                    len(search_points), search_progress + SEARCH_STEPS_PER_FRAME
                )
                if search_progress >= len(search_points):
                    animation_phase = "path"
            elif animation_phase == "path":
                path_progress = min(
                    len(path_points), path_progress + PATH_STEPS_PER_FRAME
                )
                if path_progress >= len(path_points):
                    animation_phase = "done"

        screen.fill(theme["bg"])

        ox = PADDING
        oy = PADDING

        # Draw maze tiles first so the wall graph and overlays can sit on top.
        for y in range(height):
            for x in range(width):
                rect = pygame.Rect(
                    ox + x * CELL_SIZE,
                    oy + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                is_pattern_42 = (x, y) in pattern_42_cells
                _draw_cell_tile(screen, rect, grid[y][x], theme, x, y, is_pattern_42)

        # Draw walls thick
        for y in range(height):
            for x in range(width):
                cell = grid[y][x]
                x0 = ox + x * CELL_SIZE
                y0 = oy + y * CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE

                if cell.has_wall(Direction.NORTH):
                    pygame.draw.line(
                        screen, theme["cell_wall"], (x0, y0), (x1, y0), WALL_THICKNESS
                    )
                if cell.has_wall(Direction.EAST):
                    pygame.draw.line(
                        screen, theme["cell_wall"], (x1, y0), (x1, y1), WALL_THICKNESS
                    )
                if cell.has_wall(Direction.SOUTH):
                    pygame.draw.line(
                        screen, theme["cell_wall"], (x0, y1), (x1, y1), WALL_THICKNESS
                    )
                if cell.has_wall(Direction.WEST):
                    pygame.draw.line(
                        screen, theme["cell_wall"], (x0, y0), (x0, y1), WALL_THICKNESS
                    )

        if show_path:
            if search_progress > 0:
                _draw_search_overlay(
                    screen, search_points[:search_progress], ox, oy, theme
                )
            if path_progress > 0:
                _draw_path_overlay(screen, path_points[:path_progress], ox, oy, theme)

        # Entry/Exit blocks
        ex, ey = entry
        tx, ty = exit_
        e_rect = pygame.Rect(
            ox + ex * CELL_SIZE + MARKER_INSET,
            oy + ey * CELL_SIZE + MARKER_INSET,
            CELL_SIZE - 2 * MARKER_INSET,
            CELL_SIZE - 2 * MARKER_INSET,
        )
        x_rect = pygame.Rect(
            ox + tx * CELL_SIZE + MARKER_INSET,
            oy + ty * CELL_SIZE + MARKER_INSET,
            CELL_SIZE - 2 * MARKER_INSET,
            CELL_SIZE - 2 * MARKER_INSET,
        )
        _draw_marker(screen, e_rect, theme["entry"])
        _draw_marker(screen, x_rect, theme["exit"])

        help_text = "R regenerate | P path on/off | C colors | Q/ESC quit"
        txt = font.render(help_text, True, theme["text"])
        screen.blit(txt, (PADDING, oy + maze_h + 16))

        if status_message:
            status = status_font.render(status_message, True, theme["warning"])
            screen.blit(status, (PADDING, oy + maze_h + 46))

        pygame.display.flip()

    pygame.quit()
