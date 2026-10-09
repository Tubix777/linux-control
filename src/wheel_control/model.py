from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class WheelDefinition:
    product_id: str
    name: str
    minimum_range: int
    maximum_range: int
    steering_axis: int = 0x00
    throttle_axis: int | None = 0x02
    brake_axis: int | None = 0x05
    clutch_axis: int | None = 0x01


LOGITECH_WHEELS: Mapping[str, WheelDefinition] = {
    "c24f": WheelDefinition("c24f", "Logitech G29", 40, 900),
    "c260": WheelDefinition("c260", "Logitech G29 (PS4 mode)", 40, 900),
    "c262": WheelDefinition(
        "c262",
        "Logitech G920",
        40,
        900,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c266": WheelDefinition("c266", "Logitech G923 (PlayStation)", 40, 900),
    "c26e": WheelDefinition(
        "c26e",
        "Logitech G923 (Xbox)",
        40,
        900,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c29b": WheelDefinition("c29b", "Logitech G27", 40, 900),
    "c299": WheelDefinition("c299", "Logitech G25", 40, 900),
    "c29a": WheelDefinition(
        "c29a",
        "Logitech Driving Force GT",
        40,
        900,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c298": WheelDefinition(
        "c298",
        "Logitech Driving Force Pro",
        40,
        900,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c294": WheelDefinition(
        "c294",
        "Logitech Driving Force",
        40,
        270,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c295": WheelDefinition(
        "c295",
        "Logitech MOMO Force",
        40,
        270,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "ca03": WheelDefinition(
        "ca03",
        "Logitech MOMO Racing",
        40,
        270,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c291": WheelDefinition(
        "c291",
        "Logitech WingMan Formula Force",
        40,
        180,
        steering_axis=0x08,
        throttle_axis=0x09,
        brake_axis=0x0A,
        clutch_axis=None,
    ),
    "c293": WheelDefinition(
        "c293",
        "Logitech WingMan Formula Force GP",
        40,
        180,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "ca04": WheelDefinition(
        "ca04",
        "Logitech Racing Wheel",
        40,
        270,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c20e": WheelDefinition(
        "c20e",
        "Logitech WingMan Formula GP",
        40,
        180,
        throttle_axis=0x01,
        brake_axis=0x02,
        clutch_axis=0x05,
    ),
    "c202": WheelDefinition("c202", "Logitech WingMan Formula", 40, 180),
    "c29c": WheelDefinition("c29c", "Logitech Speed Force Wireless", 40, 270),
    "c268": WheelDefinition(
        "c268",
        "Logitech G PRO Racing Wheel (PlayStation)",
        40,
        1080,
        throttle_axis=0x03,
        brake_axis=0x04,
        clutch_axis=0x05,
    ),
    "c272": WheelDefinition(
        "c272",
        "Logitech G PRO Racing Wheel (Xbox)",
        40,
        1080,
        throttle_axis=0x03,
        brake_axis=0x04,
        clutch_axis=0x05,
    ),
    "c276": WheelDefinition("c276", "Logitech RS50", 40, 2700),
}


@dataclass(slots=True)
class WheelDevice:
    name: str
    vendor_id: str
    product_id: str
    event_node: Path | None
    sysfs_path: Path | None
    driver: str = "unknown"
    firmware_revision: str | None = None
    attributes: dict[str, Path] = field(default_factory=dict)
    ff_capabilities: set[str] = field(default_factory=set)
    axis_ranges: dict[int, tuple[int, int]] = field(default_factory=dict)
    minimum_range: int = 40
    maximum_range: int = 900
    steering_axis: int = 0x00
    throttle_axis: int | None = 0x02
    brake_axis: int | None = 0x05
    clutch_axis: int | None = 0x01
    demo: bool = False
    _demo_values: dict[str, int] = field(default_factory=dict, repr=False)

    @property
    def axis_codes(self) -> dict[str, int]:
        return {
            name: code
            for name, code in {
                "steering": self.steering_axis,
                "throttle": self.throttle_axis,
                "brake": self.brake_axis,
                "clutch": self.clutch_axis,
            }.items()
            if code is not None
        }

    @property
    def identifier(self) -> str:
        if self.demo:
            return "demo:g29"
        node = self.event_node.name if self.event_node else "no-event"
        return f"{self.vendor_id}:{self.product_id}:{node}"

    def supports(self, attribute: str) -> bool:
        return attribute in self.attributes or attribute in self.ff_capabilities

    def can_write(self, attribute: str) -> bool:
        if not self.supports(attribute):
            return False
        if self.demo:
            return True
        path = self.attributes.get(attribute)
        if path is not None:
            return os.access(path, os.W_OK)
        return self.event_node is not None and os.access(self.event_node, os.W_OK)

    def read_attribute(self, attribute: str, default: int = 0) -> int:
        if self.demo:
            defaults = {
                "range": 900,
                "gain": 49151,
                "autocenter": 0,
                "combine_pedals": 0,
                "spring_level": 100,
                "damper_level": 100,
                "friction_level": 100,
                "ffb_leds": 0,
                "peak_ffb_level": 0,
            }
            return self._demo_values.get(attribute, defaults.get(attribute, default))
        path = self.attributes.get(attribute)
        if path is None:
            return default
        try:
            return int(path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return default

    def write_attribute(self, attribute: str, value: int) -> None:
        value = self.validate_attribute(attribute, value)
        if self.demo:
            self._demo_values[attribute] = value
            return
        path = self.attributes.get(attribute)
        if path is not None:
            path.write_text(f"{value}\n", encoding="utf-8")
            return
        if attribute in self.ff_capabilities and self.event_node is not None:
            from .linux_input import write_ff_control

            write_ff_control(self.event_node, attribute, value)
            return
        raise NotImplementedError(f"{attribute} is not exposed by this driver")

    def validate_attribute(self, attribute: str, value: int) -> int:
        """Validate a control value before it reaches a kernel interface."""
        value = int(value)
        limits = {
            "range": (self.minimum_range, self.maximum_range),
            "gain": (0, 65535),
            "autocenter": (0, 65535),
            "combine_pedals": (0, 1),
            "spring_level": (0, 100),
            "damper_level": (0, 100),
            "friction_level": (0, 100),
            "ffb_leds": (0, 1),
            # new-lg4ff resets this read-only peak counter by accepting zero.
            "peak_ffb_level": (0, 0),
        }
        if attribute not in limits:
            raise ValueError(f"Unknown control: {attribute}")
        minimum, maximum = limits[attribute]
        if not minimum <= value <= maximum:
            raise ValueError(
                f"{attribute} must be between {minimum} and {maximum}, got {value}"
            )
        return value

    def alternate_modes(self) -> list[tuple[str, str, bool]]:
        path = self.attributes.get("alternate_modes")
        if path is None or self.demo:
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        modes = []
        for line in lines:
            mode_id, separator, label = line.partition(":")
            mode_id = mode_id.strip()
            label = label.strip()
            if not separator or not mode_id or not label or mode_id == "native":
                continue
            selected = label.endswith("*")
            if selected:
                label = label[:-1].rstrip()
            modes.append((mode_id, label, selected))
        return modes

    def switch_mode(self, mode_id: str) -> None:
        path = self.attributes.get("alternate_modes")
        valid_ids = {item[0] for item in self.alternate_modes()}
        if path is None or mode_id not in valid_ids:
            raise ValueError(f"Unsupported mode: {mode_id}")
        path.write_text(f"{mode_id}\n", encoding="utf-8")


def demo_g29() -> WheelDevice:
    definition = LOGITECH_WHEELS["c24f"]
    return WheelDevice(
        name=f"{definition.name} — Demo",
        vendor_id="046d",
        product_id=definition.product_id,
        event_node=None,
        sysfs_path=None,
        driver="new-lg4ff (demo)",
        attributes={
            name: Path(f"/demo/{name}")
            for name in (
                "range",
                "gain",
                "autocenter",
                "combine_pedals",
                "spring_level",
                "damper_level",
                "friction_level",
                "ffb_leds",
                "peak_ffb_level",
            )
        },
        minimum_range=definition.minimum_range,
        maximum_range=definition.maximum_range,
        steering_axis=definition.steering_axis,
        throttle_axis=definition.throttle_axis,
        brake_axis=definition.brake_axis,
        clutch_axis=definition.clutch_axis,
        demo=True,
    )
