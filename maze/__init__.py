"""A-Maze-ing package."""

from maze.config import MazeConfig, load_config
from maze.errors import ConfigError, MazeError
from maze.generator import MazeData, MazeGenerator

__all__ = [
    "MazeConfig",
    "load_config",
    "MazeError",
    "ConfigError",
    "MazeData",
    "MazeGenerator",
]
