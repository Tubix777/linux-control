from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


def _integer(value: Any, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean is not an integer setting")
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("expected a finite integer setting") from exc
    return max(minimum, min(maximum, result))


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise ValueError("expected a boolean setting")


def _atomic_json_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    contents = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@dataclass(slots=True)
class WheelProfile:
    name: str
    rotation_range: int = 900
    gain: int = 75
    autocenter: int = 0
    combine_pedals: bool = False
    spring_level: int = 100
    damper_level: int = 100
    friction_level: int = 100
    ffb_leds: bool = False

    def normalised(
        self, minimum_range: int = 40, maximum_range: int = 2700
    ) -> WheelProfile:
        if not isinstance(self.name, str):
            raise ValueError("profile name must be text")
        name = self.name.strip()[:40]
        if not name:
            raise ValueError("profile name cannot be empty")
        return WheelProfile(
            name=name,
            rotation_range=_integer(self.rotation_range, minimum_range, maximum_range),
            gain=_integer(self.gain, 0, 100),
            autocenter=_integer(self.autocenter, 0, 100),
            combine_pedals=_boolean(self.combine_pedals),
            spring_level=_integer(self.spring_level, 0, 100),
            damper_level=_integer(self.damper_level, 0, 100),
            friction_level=_integer(self.friction_level, 0, 100),
            ffb_leds=_boolean(self.ffb_leds),
        )


class ProfileStore:
    def __init__(self, path: Path | None = None) -> None:
        config_root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.path = path or config_root / "wheel-control" / "profiles.json"

    def load(self) -> list[WheelProfile]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return [WheelProfile(name="Default")]
        profiles = []
        if not isinstance(data, dict) or not isinstance(data.get("profiles"), list):
            return [WheelProfile(name="Default")]
        for entry in data["profiles"]:
            if not isinstance(entry, dict):
                continue
            try:
                profiles.append(WheelProfile(**entry).normalised())
            except (TypeError, ValueError):
                continue
        return profiles or [WheelProfile(name="Default")]

    def save(self, profiles: list[WheelProfile]) -> None:
        safe_profiles = [profile.normalised() for profile in profiles]
        _atomic_json_write(
            self.path,
            {
                "version": 1,
                "profiles": [asdict(profile) for profile in safe_profiles],
            },
        )


def export_profile(profile: WheelProfile, path: Path) -> None:
    safe_profile = profile.normalised()
    _atomic_json_write(path, {"version": 1, "profile": asdict(safe_profile)})


def import_profile(path: Path, name: str | None = None) -> WheelProfile:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("profile file is not valid JSON") from exc
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("unsupported profile file version")
    entry = data.get("profile")
    if not isinstance(entry, dict):
        raise ValueError("profile file does not contain a profile")
    if name is not None:
        entry = {**entry, "name": name}
    try:
        return WheelProfile(**entry).normalised()
    except TypeError as exc:
        raise ValueError("profile file contains unknown fields") from exc
