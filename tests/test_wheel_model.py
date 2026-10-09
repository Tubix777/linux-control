import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wheel_control.model import LOGITECH_WHEELS, WheelDevice, demo_g29


class ModelTests(unittest.TestCase):
    def test_write_access_distinguishes_sysfs_from_evdev(self):
        device = WheelDevice(
            name="Test",
            vendor_id="046d",
            product_id="c24f",
            event_node=Path("/dev/input/event-test"),
            sysfs_path=None,
            attributes={"range": Path("/sys/test/range")},
            ff_capabilities={"gain"},
        )
        with patch(
            "wheel_control.model.os.access",
            side_effect=lambda path, mode: path == device.event_node,
        ):
            self.assertFalse(device.can_write("range"))
            self.assertTrue(device.can_write("gain"))
            self.assertFalse(device.can_write("unknown"))

    def test_g29_definition(self) -> None:
        definition = LOGITECH_WHEELS["c24f"]
        self.assertEqual(definition.name, "Logitech G29")
        self.assertEqual(definition.maximum_range, 900)

    def test_demo_supports_mvp_controls(self) -> None:
        device = demo_g29()
        self.assertTrue(device.demo)
        self.assertTrue(device.supports("range"))
        self.assertTrue(device.supports("gain"))
        self.assertEqual(device.read_attribute("range"), 900)

    def test_legacy_ranges_match_hardware(self) -> None:
        self.assertEqual(LOGITECH_WHEELS["c294"].maximum_range, 270)
        self.assertEqual(LOGITECH_WHEELS["c291"].maximum_range, 180)
        self.assertEqual(LOGITECH_WHEELS["c293"].maximum_range, 180)

    def test_device_families_use_their_real_pedal_layout(self) -> None:
        self.assertEqual(LOGITECH_WHEELS["c24f"].throttle_axis, 0x02)
        self.assertEqual(LOGITECH_WHEELS["c262"].throttle_axis, 0x01)
        self.assertEqual(LOGITECH_WHEELS["c268"].throttle_axis, 0x03)
        self.assertEqual(LOGITECH_WHEELS["c291"].steering_axis, 0x08)
        self.assertIsNone(LOGITECH_WHEELS["c291"].clutch_axis)

    def test_rejects_out_of_range_kernel_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gain"
            path.write_text("0\n", encoding="utf-8")
            device = WheelDevice(
                name="Test",
                vendor_id="046d",
                product_id="c24f",
                event_node=None,
                sysfs_path=Path(directory),
                attributes={"gain": path},
            )
            with self.assertRaises(ValueError):
                device.write_attribute("gain", 65536)
            self.assertEqual(path.read_text(encoding="utf-8"), "0\n")


if __name__ == "__main__":
    unittest.main()
