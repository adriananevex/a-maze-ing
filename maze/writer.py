"""Output writer for maze file format."""

from __future__ import annotations

from pathlib import Path
from maze.models import Cell


def write_maze_file(
    output_file: str,
    grid: list[list[Cell]],
    entry: tuple[int, int],
    exit_: tuple[int, int],
    path_letters: str,
) -> None:
    """Write maze in required format: hex rows + metadata block."""
    out_path = Path(output_file)

    lines: list[str] = []
    for row in grid:
        lines.append("".join(cell.to_hex() for cell in row))

    lines.append("")
    lines.append(f"{entry[0]}, {entry[1]}")
    lines.append(f"{exit_[0]}, {exit_[1]}")
    lines.append(path_letters)

    content = "\n".join(lines) + "\n"
    with out_path.open("w", encoding="utf-8") as file:
        file.write(content)
