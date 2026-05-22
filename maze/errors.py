"""Custom exceptions for the A-Maze-ing project."""


class MazeError(Exception):
    """Base exception for all maze-related errors."""


class ConfigError(MazeError):
    """Raised when configuration parsing or validation fails."""
