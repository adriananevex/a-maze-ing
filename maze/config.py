"""Configuration parsing and validation for the A-Maze-ing project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from maze.errors import ConfigError


@dataclass(frozen=True)
class MazeConfig:
    """Validated maze configuration."""

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None = None
    display: str = "NONE"


_REQUIRED_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}
_OPTIONAL_KEYS = {"SEED", "DISPLAY"}


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ConfigError(f"Invalid boolean value: {value!r}")


def _parse_int(value: str, key: str) -> int:
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ConfigError(f"Invalid integer for {key}: {value!r}") from exc


def _parse_coords(value: str, key: str) -> tuple[int, int]:
    parts = value.split(",")
    if len(parts) != 2:
        raise ConfigError(f"Invalid coordinate format for {key}: {value!r}. Expected x,y")
    try:
        x = int(parts[0].strip())
        y = int(parts[1].strip())
    except ValueError as exc:
        raise ConfigError(f"Invalid coordinate integers for {key}: {value!r}") from exc
    return (x, y)


def _read_raw_config(path: Path) -> Dict[str, str]:
    raw: Dict[str, str] = {}
    try:
        with path.open("r", encoding="utf-8") as file:
            for line_no, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    raise ConfigError(
                        f"Invalid config syntax at line {line_no}: {stripped!r}. "
                        "Expected KEY=VALUE."
                    )
                key, value = stripped.split("=", 1)
                key = key.strip().upper()
                value = value.strip()
                if not key:
                    raise ConfigError(f"Empty key at line {line_no}.")
                raw[key] = value
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file not found: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read configuration file: {path}") from exc
    return raw


def load_config(path_str: str) -> MazeConfig:
    """Load and validate the maze configuration file."""
    path = Path(path_str)
    raw = _read_raw_config(path)

    missing = _REQUIRED_KEYS - set(raw.keys())
    if missing:
        raise ConfigError(f"Missing mandatory config keys: {sorted(missing)}")

    unknown = set(raw.keys()) - _REQUIRED_KEYS - _OPTIONAL_KEYS
    if unknown:
        raise ConfigError(f"Unknown config keys: {sorted(unknown)}")

    width = _parse_int(raw["WIDTH"], "WIDTH")
    height = _parse_int(raw["HEIGHT"], "HEIGHT")
    entry = _parse_coords(raw["ENTRY"], "ENTRY")
    exit_ = _parse_coords(raw["EXIT"], "EXIT")
    output_file = raw["OUTPUT_FILE"].strip()
    perfect = _parse_bool(raw["PERFECT"])
    seed = _parse_int(raw["SEED"], "SEED") if "SEED" in raw else None
    display = raw.get("DISPLAY", "NONE").strip().upper()

    if width <= 0 or height <= 0:
        raise ConfigError("WIDTH and HEIGHT must be positive integers.")

    if output_file == "":
        raise ConfigError("OUTPUT_FILE cannot be empty.")

    if display not in {"NONE", "ASCII", "GUI"}:
        raise ConfigError("DISPLAY must be either NONE, ASCII, or GUI.")

    ex, ey = entry
    xx, xy = exit_

    if not (0 <= ex < width and 0 <= ey < height):
        raise ConfigError(f"ENTRY out of bounds: {entry} for WIDTH={width}, HEIGHT={height}")
    if not (0 <= xx < width and 0 <= xy < height):
        raise ConfigError(f"EXIT out of bounds: {exit_} for WIDTH={width}, HEIGHT={height}")
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must be different.")

    return MazeConfig(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=output_file,
        perfect=perfect,
        seed=seed,
        display=display,
    )
