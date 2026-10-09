"""Local appearance preferences, independent of wheel settings."""

import json
import os
from pathlib import Path

from .profiles import _atomic_json_write

THEMES = {"black": "Black", "graphite": "Graphite", "light": "Light"}
PALETTES = {
    "black": ("#101010", "#191919", "#eeeeee", "#333333", "#809bb7"),
    "graphite": ("#25272a", "#303236", "#f0f0f0", "#46494e", "#91abc5"),
    "light": ("#eeeeec", "#ffffff", "#242424", "#d1d1cd", "#315f89"),
}


class AppearanceStore:
    def __init__(self, path: Path | None = None):
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.path = path or root / "wheel-control" / "appearance.json"

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def load(self) -> str:
        theme = self._read().get("theme")
        return theme if isinstance(theme, str) and theme in THEMES else "black"

    def load_reduced_motion(self) -> bool:
        return self._read().get("reduced_motion") is True

    def save_reduced_motion(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ValueError("Reduced motion must be a boolean")
        data = self._read()
        data.update(version=1, reduced_motion=enabled)
        _atomic_json_write(self.path, data)

    def save(self, theme: str) -> None:
        if theme not in THEMES:
            raise ValueError("Unknown appearance")
        data = self._read()
        data.update(version=1, theme=theme)
        _atomic_json_write(self.path, data)


def palette_css(theme: str) -> str:
    background, surface, foreground, border, accent = PALETTES[theme]
    colors = {}
    for prefix in ("window", "view", "headerbar", "card", "popover", "dialog"):
        colors[f"{prefix}_bg_color"] = (
            surface if prefix in ("card", "popover", "dialog") else background
        )
        colors[f"{prefix}_fg_color"] = foreground
    colors.update(
        headerbar_backdrop_color=background,
        accent_color=accent,
        accent_bg_color=accent,
        accent_fg_color="#ffffff" if theme == "light" else "#101010",
        wheel_border=border,
    )
    return "\n".join(f"@define-color {key} {value};" for key, value in colors.items())
