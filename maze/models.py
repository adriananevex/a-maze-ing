"""Core data structures for maze representation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

class Direction(Enum):
    """Cardinal directions with bit position and coordinate delta."""

    NORTH = (0, 0, -1, "N")
    EAST = (1, 1, 0, "E")
    SOUTH = (2, 0, 1, "S")
    WEST = (3, -1, 0, "W")

    @property
    def bit(self) -> int:
        """Return bit index used in hex wall encoding."""
        return self.value[0]
    
    @property
    def dx(self) -> int:
        """Return x-axis delta."""
        return self.value[1]

    @property
    def dy(self) -> int:
        """Return y-axis delta."""
        return self.value[2]

    @property
    def letter(self) -> str:
        """Return single-letter movement representation."""
        return self.value[3]
    
    @property
    def opposite(self) -> "Direction":
        """Return opposite cardinal direction."""
        if self is Direction.NORTH:
            return Direction.SOUTH
        if self is Direction.SOUTH:
            return Direction.NORTH
        if self is Direction.EAST:
            return Direction.WEST
        return Direction.EAST

ALL_DIRECTIONS: tuple[Direction, ...] = (
    Direction.NORTH,
    Direction.EAST,
    Direction.SOUTH,
    Direction.WEST,
)

@dataclass
class Cell:
    """Single maze cell with 4 walls and visit state."""

    walls: int = 0b1111
    visited: bool = False

    def has_wall(self, direction: Direction) -> bool:
        """Check if wall is closed in given direction."""
        return bool(self.walls & (1 << direction.bit))

    def set_wall(self, direction: Direction, closed: bool) -> None:
        """Open or close wall in given direction."""
        mask = 1 << direction.bit
        if closed:
            self.walls |= mask
        else:
            self.walls &= ~mask
    
    def to_hex(self) -> str:
        """Encode cell walls as uppercase hexadecimal digit."""
        return format(self.walls, "X")