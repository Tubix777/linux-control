import unittest
from pathlib import Path
from unittest.mock import patch

from wheel_control.linux_input import (
    _ABS_INFO,
    _EVENT,
    LinuxInputReader,
    _bit_is_set,
    _ior,
    absolute_axis_capabilities,
)


class LinuxInputTests(unittest.TestCase):
    def test_bit_reader(self) -> None:
        self.assertTrue(_bit_is_set(bytes([0b00000100]), 2))
        self.assertFalse(_bit_is_set(bytes([0b00000100]), 3))
        self.assertFalse(_bit_is_set(b"", 2))

    def test_axis_normalisation(self) -> None:
        self.assertEqual(LinuxInputReader._normalise(0, 0, 100), 0.0)
        self.assertEqual(LinuxInputReader._normalise(50, 0, 100), 0.5)
        self.assertEqual(LinuxInputReader._normalise(100, 0, 100, True), 0.0)
        self.assertEqual(LinuxInputReader._normalise(0, 0, 100, True), 1.0)
        self.assertEqual(LinuxInputReader._normalise(5, 10, 10), 0.0)

    def test_absolute_axis_probe_returns_supported_ranges(self) -> None:
        x_request = _ior("E", 0x40, _ABS_INFO.size)

        def ioctl(_descriptor, request, _buffer):
            if request == _ior("E", 0x23, 8):
                return bytes([1]) + bytes(7)
            if request == x_request:
                return _ABS_INFO.pack(32767, 0, 65535, 0, 0, 1)
            raise OSError

        with (
            patch("wheel_control.linux_input.os.open", return_value=9),
            patch("wheel_control.linux_input.os.close") as close,
            patch("wheel_control.linux_input.fcntl.ioctl", side_effect=ioctl),
        ):
            self.assertEqual(
                absolute_axis_capabilities(Path("/dev/input/event0")),
                {0: (0, 65535)},
            )
            close.assert_called_once_with(9)

    def test_initial_snapshot_without_input_events(self) -> None:
        reader = LinuxInputReader(
            Path("/unused"), lambda value: snapshots.append(value)
        )
        snapshots = []
        reader._descriptor = 9
        reader._axis_info = {0: (0, 100), 2: (0, 255)}
        reader._initial_values = {0: 75, 2: 255}
        reader._stop.set()
        reader._run()
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].steering, 0.5)
        self.assertEqual(snapshots[0].throttle, 0)

    def test_dropped_events_requery_state_and_ignore_stale_buttons(self) -> None:
        from wheel_control.telemetry import Telemetry

        snapshots = []
        reader = LinuxInputReader(Path("/unused"), snapshots.append)
        reader._descriptor = 9
        data = b"".join(
            _EVENT.pack(0, 0, *event)
            for event in (
                (0, 3, 0),  # SYN_DROPPED
                (1, 288, 1),  # Stale button event must be ignored.
                (0, 0, 0),  # SYN_REPORT: resynchronise with ioctl.
            )
        )
        with (
            patch.object(
                reader, "_snapshot", side_effect=[Telemetry(), Telemetry(steering=0.75)]
            ) as snapshot,
            patch(
                "wheel_control.linux_input.select.select", return_value=([9], [], [])
            ),
            patch("wheel_control.linux_input.os.read", side_effect=[data, b""]),
        ):
            reader._run()
        snapshot.assert_called_with(refresh=True)
        self.assertEqual(snapshots[-1].steering, 0.75)
        self.assertEqual(snapshots[-1].pressed_buttons, ())


if __name__ == "__main__":
    unittest.main()
