from __future__ import annotations

import fcntl
import os
import select
import struct
import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from .telemetry import Telemetry

EV_ABS = 0x03
EV_SYN = 0x00
SYN_REPORT = 0
SYN_DROPPED = 3
EV_KEY = 0x01
EV_FF = 0x15
ABS_X = 0x00
ABS_Y = 0x01
ABS_Z = 0x02
ABS_RZ = 0x05
ABS_HAT0X = 0x10
ABS_HAT0Y = 0x11
ABS_MAX = 0x3F
FF_GAIN = 0x60
FF_AUTOCENTER = 0x61

_EVENT = struct.Struct("@llHHi")
_ABS_INFO = struct.Struct("@iiiiii")

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS
_IOC_READ = 2


def _ior(type_: str, number: int, size: int) -> int:
    return (
        (_IOC_READ << _IOC_DIRSHIFT)
        | (ord(type_) << _IOC_TYPESHIFT)
        | (number << _IOC_NRSHIFT)
        | (size << _IOC_SIZESHIFT)
    )


def _bit_is_set(data: bytes, bit: int) -> bool:
    byte_index, bit_index = divmod(bit, 8)
    return byte_index < len(data) and bool(data[byte_index] & (1 << bit_index))


def force_feedback_capabilities(event_node: Path) -> set[str]:
    length = 16
    request = _ior("E", 0x20 + EV_FF, length)
    try:
        descriptor = os.open(event_node, os.O_RDONLY | os.O_NONBLOCK)
        try:
            data = fcntl.ioctl(descriptor, request, bytes(length))
        finally:
            os.close(descriptor)
    except OSError:
        return set()
    capabilities = set()
    if _bit_is_set(data, FF_GAIN):
        capabilities.add("gain")
    if _bit_is_set(data, FF_AUTOCENTER):
        capabilities.add("autocenter")
    return capabilities


def absolute_axis_capabilities(event_node: Path) -> dict[int, tuple[int, int]]:
    """Return the raw minimum and maximum for every exposed absolute axis."""
    try:
        descriptor = os.open(event_node, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        return {}
    axes: dict[int, tuple[int, int]] = {}
    try:
        try:
            supported = fcntl.ioctl(descriptor, _ior("E", 0x20 + EV_ABS, 8), bytes(8))
        except OSError:
            return {}
        for code in range(ABS_MAX + 1):
            if not _bit_is_set(supported, code):
                continue
            request = _ior("E", 0x40 + code, _ABS_INFO.size)
            try:
                result = fcntl.ioctl(descriptor, request, bytes(_ABS_INFO.size))
            except OSError:
                continue
            _value, minimum, maximum, _fuzz, _flat, _resolution = _ABS_INFO.unpack(
                result
            )
            axes[code] = (minimum, maximum)
    finally:
        os.close(descriptor)
    return axes


def write_ff_control(event_node: Path, control: str, value: int) -> None:
    codes = {"gain": FF_GAIN, "autocenter": FF_AUTOCENTER}
    try:
        code = codes[control]
    except KeyError as exc:
        raise NotImplementedError(control) from exc
    descriptor = os.open(event_node, os.O_RDWR | os.O_NONBLOCK)
    try:
        os.write(descriptor, _EVENT.pack(0, 0, EV_FF, code, max(0, min(65535, value))))
    finally:
        os.close(descriptor)


class LinuxInputReader:
    def __init__(
        self,
        event_node: Path,
        callback: Callable[[Telemetry], None],
        axis_codes: dict[str, int] | None = None,
    ) -> None:
        self.event_node = event_node
        self.callback = callback
        self._descriptor: int | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._axis_info: dict[int, tuple[int, int]] = {}
        self._initial_values: dict[int, int] = {}
        self.axis_codes = axis_codes or {
            "steering": ABS_X,
            "throttle": ABS_Z,
            "brake": ABS_RZ,
            "clutch": ABS_Y,
        }

    def start(self) -> bool:
        if self._thread and self._thread.is_alive():
            return True
        if self._descriptor is not None:
            self.stop()
        self._stop.clear()
        self._axis_info.clear()
        self._initial_values.clear()
        try:
            self._descriptor = os.open(self.event_node, os.O_RDONLY | os.O_NONBLOCK)
            for code in {*self.axis_codes.values(), ABS_HAT0X, ABS_HAT0Y}:
                request = _ior("E", 0x40 + code, _ABS_INFO.size)
                try:
                    result = fcntl.ioctl(
                        self._descriptor, request, bytes(_ABS_INFO.size)
                    )
                    value, minimum, maximum, _fuzz, _flat, _resolution = (
                        _ABS_INFO.unpack(result)
                    )
                    self._axis_info[code] = (minimum, maximum)
                    self._initial_values[code] = value
                except OSError:
                    continue
        except OSError:
            self.stop()
            return False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        if self._descriptor is not None:
            try:
                os.close(self._descriptor)
            except OSError:
                pass
            self._descriptor = None

    @staticmethod
    def _normalise(
        value: int, minimum: int, maximum: int, invert: bool = False
    ) -> float:
        if maximum <= minimum:
            return 0.0
        result = max(0.0, min(1.0, (value - minimum) / (maximum - minimum)))
        return 1.0 - result if invert else result

    def _snapshot(self, refresh: bool = False) -> Telemetry:
        assert self._descriptor is not None
        if refresh:
            for code in self._axis_info:
                try:
                    result = fcntl.ioctl(
                        self._descriptor,
                        _ior("E", 0x40 + code, _ABS_INFO.size),
                        bytes(_ABS_INFO.size),
                    )
                    self._initial_values[code] = _ABS_INFO.unpack(result)[0]
                except OSError:
                    continue
        telemetry = Telemetry()
        for field, code in self.axis_codes.items():
            if code in self._initial_values:
                minimum, maximum = self._axis_info[code]
                value = self._normalise(
                    self._initial_values[code], minimum, maximum, field != "steering"
                )
                setattr(
                    telemetry, field, value * 2 - 1 if field == "steering" else value
                )
        telemetry.hat_x = self._initial_values.get(ABS_HAT0X, 0)
        telemetry.hat_y = self._initial_values.get(ABS_HAT0Y, 0)
        try:
            buttons = fcntl.ioctl(self._descriptor, _ior("E", 0x18, 96), bytes(96))
            telemetry.pressed_buttons = tuple(
                code for code in range(768) if _bit_is_set(buttons, code)
            )
        except OSError:
            pass
        return telemetry

    def _run(self) -> None:
        assert self._descriptor is not None
        telemetry = self._snapshot()
        # Publish stationary controls before waiting for the first changed event.
        self.callback(replace(telemetry))
        pressed_buttons = set(telemetry.pressed_buttons)
        axis_map = {
            code: (name, name != "steering") for name, code in self.axis_codes.items()
        }
        buffer = b""
        dropped = False
        while not self._stop.is_set():
            try:
                readable, _, _ = select.select([self._descriptor], [], [], 0.1)
            except (OSError, ValueError):
                return
            if not readable:
                continue
            try:
                chunk = os.read(self._descriptor, _EVENT.size * 32)
            except BlockingIOError:
                continue
            except OSError:
                return
            if not chunk:
                return
            buffer += chunk
            changed = False
            while len(buffer) >= _EVENT.size:
                raw, buffer = buffer[: _EVENT.size], buffer[_EVENT.size :]
                _seconds, _microseconds, event_type, code, value = _EVENT.unpack(raw)
                if event_type == EV_SYN and code == SYN_DROPPED:
                    dropped = True
                    changed = False
                    continue
                if dropped:
                    if event_type == EV_SYN and code == SYN_REPORT:
                        telemetry = self._snapshot(refresh=True)
                        pressed_buttons = set(telemetry.pressed_buttons)
                        dropped = False
                        changed = True
                    continue
                if event_type == EV_KEY:
                    if value:
                        pressed_buttons.add(code)
                    else:
                        pressed_buttons.discard(code)
                    telemetry.pressed_buttons = tuple(sorted(pressed_buttons))
                    changed = True
                    continue
                if event_type != EV_ABS:
                    continue
                if code == ABS_HAT0X:
                    telemetry.hat_x = max(-1, min(1, value))
                    changed = True
                    continue
                if code == ABS_HAT0Y:
                    telemetry.hat_y = max(-1, min(1, value))
                    changed = True
                    continue
                if code not in axis_map or code not in self._axis_info:
                    continue
                field, invert = axis_map[code]
                minimum, maximum = self._axis_info[code]
                normalised = self._normalise(value, minimum, maximum, invert)
                if field == "steering":
                    normalised = normalised * 2.0 - 1.0
                setattr(telemetry, field, normalised)
                changed = True
            if changed and not dropped:
                self.callback(
                    Telemetry(
                        telemetry.steering,
                        telemetry.throttle,
                        telemetry.brake,
                        telemetry.clutch,
                        telemetry.hat_x,
                        telemetry.hat_y,
                        telemetry.pressed_buttons,
                    )
                )
