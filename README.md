*This project has been created as part of the 42 curriculum by jouarte and aneves.*

# A-Maze-ing

## Description

A-Maze-ing is a Python project that generates random mazes from a plain-text configuration file, writes the maze in the required hexadecimal wall format, and displays the result in a terminal-based ASCII view.

The project supports reproducible generation via seed, shortest-path solving, optional non-perfect mazes, and a reusable maze generation module that can be imported from other Python projects.

## Instructions

Requirements:

- Python 3.10 or later
- `pip`

Install dependencies:

```bash
make install
```

Run the program:

```bash
make run
```

Or directly:

```bash
python3 a_maze_ing.py config_default.txt
```

Debug mode:

```bash
make debug
```

Lint:

```bash
make lint
```

Clean generated files:

```bash
make clean
```

## Configuration File

The configuration file contains one `KEY=VALUE` pair per line.

Supported keys:

- `WIDTH`: maze width in cells.
- `HEIGHT`: maze height in cells.
- `ENTRY`: entry coordinates in the form `x,y`.
- `EXIT`: exit coordinates in the form `x,y`.
- `OUTPUT_FILE`: destination file for the generated maze.
- `PERFECT`: `True` or `False`.
- `SEED`: optional integer seed for reproducible generation.
- `DISPLAY`: optional display mode, one of `NONE`, `ASCII`, or `GUI`.

Example:

```text
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze_output.txt
PERFECT=False
SEED=440
DISPLAY=ASCII
```

Comments start with `#` and are ignored.

## Maze Generation Algorithm

The generator uses iterative depth-first search backtracking to create a perfect maze first, then optionally adds a limited number of extra passages when `PERFECT=False`.

This algorithm was chosen because it is simple, deterministic with a seed, easy to validate, and naturally produces coherent wall connectivity.

## Reusable Module

The reusable part of the project is the `maze` package, especially `maze.generator.MazeGenerator`.

Basic usage:

```python
from maze.generator import MazeGenerator

generator = MazeGenerator(width=20, height=15, seed=440)
maze = generator.generate(perfect=True)
```

The generated object exposes the maze grid, metadata, and whether the `42` pattern was applied. The shortest path can be computed with `maze.solver.shortest_path_letters`.

## Project Management

- Jober Duarte: maze generation, file output, configuration handling, and CLI integration.
- Adriana Neves: visual rendering, interaction flow, and presentation details.

The plan evolved from a minimal generator + writer into a project with reproducible generation, validation, ASCII visualization, and reusable importable code.

What worked well: separating configuration, generation, solving, and rendering into distinct modules.

What could be improved: reduce duplicated rendering logic, add automated tests, and tighten style/type coverage further.

Tools used:

- Python standard library
- `flake8`
- `mypy`
- `pytest` ready in the Makefile

## Resources

- Python documentation: https://docs.python.org/3/
- `dataclasses` documentation: https://docs.python.org/3/library/dataclasses.html
- `typing` documentation: https://docs.python.org/3/library/typing.html
- `mypy` documentation: https://mypy.readthedocs.io/
- `flake8` documentation: https://flake8.pycqa.org/

AI was used to review the repository against the subject, identify missing requirements, and help draft documentation and corrective code changes.