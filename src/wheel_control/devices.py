from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

import pyudev

from .linux_input import absolute_axis_capabilities, force_feedback_capabilities
from .model import LOGITECH_WHEELS, WheelDevice

CONTROL_ATTRIBUTES = (
    "range",
    "gain",
    "autocenter",
    "combine_pedals",
    "spring_level",
    "damper_level",
    "friction_level",
    "ffb_leds",
    "peak_ffb_level",
    "alternate_modes",
)


def _property(device: pyudev.Device, name: str) -> str | None:
    current: pyudev.Device | None = device
    while current is not None:
        value = current.properties.get(name)
        if value:
            return str(value).lower()
        current = current.parent
    return None


def _attribute(device: pyudev.Device, name: str) -> str | None:
    current: pyudev.Device | None = device
    while current is not None:
        try:
            value = current.attributes.asstring(name)
        except (KeyError, OSError):
            value = None
        if value:
            return value.strip().lower()
        current = current.parent
    return None


def _find_control_root(event_path: Path) -> Path | None:
    try:
        resolved_event = event_path.resolve()
    except OSError:
        return None

    candidates: list[Path] = []
    current = resolved_event
    while current != current.parent:
        candidates.append(current)
        current = current.parent

    hid_drivers = Path("/sys/bus/hid/drivers")
    if hid_drivers.exists():
        for driver in hid_drivers.iterdir():
            if not driver.is_dir():
                continue
            for link in driver.iterdir():
                if ":" not in link.name:
                    continue
                try:
                    resolved = link.resolve()
                except OSError:
                    continue
                if resolved_event == resolved or resolved_event.is_relative_to(
                    resolved
                ):
                    candidates.insert(0, link)

    for candidate in candidates:
        if any((candidate / name).exists() for name in CONTROL_ATTRIBUTES):
            return candidate
    return None


def _driver_name(control_root: Path | None) -> str:
    if control_root is None:
        return "kernel"
    driver_link = control_root / "driver"
    try:
        return driver_link.resolve().name
    except OSError:
        return control_root.parent.name if control_root.parent else "kernel"


def discover_wheels(context: pyudev.Context | None = None) -> list[WheelDevice]:
    context = context or pyudev.Context()
    discovered: list[WheelDevice] = []
    seen_nodes: set[str] = set()

    for device in context.list_devices(subsystem="input"):
        node = device.device_node
        if not node or not Path(node).name.startswith("event") or node in seen_nodes:
            continue

        vendor_id = _property(device, "ID_VENDOR_ID") or _attribute(device, "idVendor")
        product_id = _property(device, "ID_MODEL_ID") or _attribute(device, "idProduct")
        if vendor_id != "046d" or not product_id:
            continue

        definition = LOGITECH_WHEELS.get(product_id)
        is_joystick = _property(device, "ID_INPUT_JOYSTICK") == "1"
        if definition is None and not is_joystick:
            continue

        event_path = Path(device.sys_path)
        control_root = _find_control_root(event_path)
        attributes = {}
        if control_root:
            attributes = {
                name: control_root / name
                for name in CONTROL_ATTRIBUTES
                if (control_root / name).exists()
            }

        device_name = (
            definition.name
            if definition
            else (
                _property(device, "ID_MODEL_FROM_DATABASE")
                or _property(device, "ID_MODEL")
                or f"Logitech wheel {product_id}"
            )
        )
        discovered.append(
            WheelDevice(
                name=device_name.replace("_", " "),
                vendor_id=vendor_id,
                product_id=product_id,
                event_node=Path(node),
                sysfs_path=control_root,
                driver=(
                    _driver_name(control_root)
                    if control_root
                    else (_property(device, "ID_USB_DRIVER") or "kernel")
                ),
                firmware_revision=_property(device, "ID_REVISION"),
                attributes=attributes,
                ff_capabilities=force_feedback_capabilities(Path(node)),
                axis_ranges=absolute_axis_capabilities(Path(node)),
                minimum_range=definition.minimum_range if definition else 40,
                maximum_range=definition.maximum_range if definition else 900,
                steering_axis=definition.steering_axis if definition else 0x00,
                throttle_axis=definition.throttle_axis if definition else 0x02,
                brake_axis=definition.brake_axis if definition else 0x05,
                clutch_axis=definition.clutch_axis if definition else 0x01,
            )
        )
        seen_nodes.add(node)

    return sorted(discovered, key=lambda item: item.name.lower())


def available_attribute_names(device: WheelDevice) -> Iterable[str]:
    return device.attributes.keys()


class DeviceMonitor:
    """Watch input-device changes without blocking GTK's main loop."""

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem="input")
        self.observer = pyudev.MonitorObserver(
            self.monitor,
            callback=self._on_event,
            name="wheel-control-udev",
        )

    def _on_event(self, action: str, device: pyudev.Device) -> None:
        if action not in {"add", "remove", "change", "bind", "unbind"}:
            return
        node = device.device_node or ""
        if node and not Path(node).name.startswith(("event", "js")):
            return
        self.callback()

    def start(self) -> None:
        self.observer.start()

    def stop(self) -> None:
        if self.observer.is_alive():
            self.observer.stop()
