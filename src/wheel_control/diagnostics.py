from __future__ import annotations

import json
import os
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .model import WheelDevice

AXIS_NAMES = {
    0x00: "X",
    0x01: "Y",
    0x02: "Z",
    0x03: "RX",
    0x04: "RY",
    0x05: "RZ",
    0x06: "THROTTLE",
    0x07: "RUDDER",
    0x08: "WHEEL",
    0x09: "GAS",
    0x0A: "BRAKE",
    0x10: "HAT0X",
    0x11: "HAT0Y",
}


def _path_access(path: Path | None) -> dict[str, bool] | None:
    if path is None:
        return None
    return {
        "exists": path.exists(),
        "readable": os.access(path, os.R_OK),
        "writable": os.access(path, os.W_OK),
    }


def device_diagnostics(device: WheelDevice) -> dict[str, Any]:
    attributes = {}
    for name, path in sorted(device.attributes.items()):
        try:
            value: str | None = path.read_text(encoding="utf-8").strip()
        except OSError:
            value = None
        attributes[name] = {
            "path": str(path),
            "value": value,
            "access": _path_access(path),
        }
    recommendations: list[dict[str, str]] = []
    locked = [
        name
        for name in (*device.attributes, *device.ff_capabilities)
        if not device.can_write(name)
    ]
    if locked and not device.demo:
        recommendations.append(
            {
                "code": "control-permission",
                "message": f"Read-only controls: {', '.join(sorted(set(locked)))}. An administrator must install the packaged udev rule; then reconnect the wheel.",
            }
        )
    if device.product_id == "c260":
        recommendations.append(
            {
                "code": "g29-ps4-mode",
                "message": "Move the G29 selector to PS3 mode and reconnect USB.",
            }
        )
    if device.event_node and not os.access(device.event_node, os.R_OK):
        recommendations.append(
            {
                "code": "event-permission",
                "message": "Install the packaged udev rule and reconnect the wheel.",
            }
        )
    if not device.attributes and not device.ff_capabilities:
        recommendations.append(
            {
                "code": "no-controls",
                "message": "The active driver exposes input only and no configurable controls.",
            }
        )
    return {
        "name": device.name,
        "identifier": device.identifier,
        "usb_id": f"{device.vendor_id}:{device.product_id}",
        "driver": device.driver,
        "firmware_revision": device.firmware_revision,
        "event_node": str(device.event_node) if device.event_node else None,
        "event_access": _path_access(device.event_node),
        "sysfs_path": str(device.sysfs_path) if device.sysfs_path else None,
        "range": {"minimum": device.minimum_range, "maximum": device.maximum_range},
        "axis_codes": device.axis_codes,
        "input_axes": [
            {
                "code": code,
                "name": AXIS_NAMES.get(code, f"ABS_{code:02X}"),
                "minimum": limits[0],
                "maximum": limits[1],
            }
            for code, limits in sorted(device.axis_ranges.items())
        ],
        "force_feedback_controls": sorted(device.ff_capabilities),
        "attributes": attributes,
        "recommendations": recommendations,
        "demo": device.demo,
    }


def build_diagnostics(devices: list[WheelDevice]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "wheel_control_version": __version__,
        "system": {
            "kernel": platform.release(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "desktop": os.environ.get("XDG_CURRENT_DESKTOP"),
            "session_type": os.environ.get("XDG_SESSION_TYPE"),
        },
        "devices": [device_diagnostics(device) for device in devices],
    }


def diagnostics_json(devices: list[WheelDevice]) -> str:
    return json.dumps(build_diagnostics(devices), indent=2, ensure_ascii=False) + "\n"
