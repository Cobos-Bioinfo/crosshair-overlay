"""Crosshair settings model and JSON persistence.

The crosshair is described by a small, composable set of fields rather than a
fixed list of styles: toggle the arms, the center dot and the surrounding
circle independently to build classic, dot, T-shape, circle or hybrid reticles.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

APP_NAME = "crosshair-overlay"


def default_config_path() -> Path:
    """Return the per-user config path for the current platform."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME / "config.json"


@dataclass
class Settings:
    """All tunable properties of the crosshair."""

    # Center cross arms.
    show_lines: bool = True
    length: int = 8
    thickness: int = 2
    gap: int = 4
    t_shape: bool = False  # Hide the top arm for a "T" reticle.

    # Center dot.
    show_dot: bool = True
    dot_size: int = 3

    # Surrounding circle.
    show_circle: bool = False
    circle_radius: int = 16
    circle_thickness: int = 2

    # Appearance.
    color: str = "#00FF00"
    opacity: int = 100  # 0-100
    outline: bool = True
    outline_color: str = "#000000"
    outline_thickness: int = 1

    # Placement.
    offset_x: int = 0
    offset_y: int = 0
    monitor: int = 0  # Screen index; 0 = primary.

    @classmethod
    def from_dict(cls, data: dict) -> Settings:
        """Build Settings from a dict, ignoring unknown keys."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict:
        return asdict(self)


def load_settings(path: Path) -> Settings:
    """Load settings from ``path``; fall back to defaults on any problem."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return Settings()
    if not isinstance(data, dict):
        return Settings()
    return Settings.from_dict(data)


def save_settings(settings: Settings, path: Path) -> None:
    """Persist ``settings`` to ``path`` as pretty JSON, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings.to_dict(), indent=2) + "\n", encoding="utf-8")
