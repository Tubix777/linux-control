import tempfile
import unittest
from pathlib import Path

from wheel_control.model import WheelDevice


class AlternateModeTests(unittest.TestCase):
    def test_parse_and_switch_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alternate_modes"
            path.write_text(
                "native: G29\ng27: G27 compatibility *\ndfp: Driving Force Pro\n",
                encoding="utf-8",
            )
            device = WheelDevice(
                name="Test",
                vendor_id="046d",
                product_id="c24f",
                event_node=None,
                sysfs_path=Path(directory),
                attributes={"alternate_modes": path},
            )
            self.assertEqual(
                device.alternate_modes(),
                [
                    ("g27", "G27 compatibility", True),
                    ("dfp", "Driving Force Pro", False),
                ],
            )
            device.switch_mode("dfp")
            self.assertEqual(path.read_text(encoding="utf-8"), "dfp\n")

    def test_reject_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alternate_modes"
            path.write_text("g27: G27\n", encoding="utf-8")
            device = WheelDevice(
                name="Test",
                vendor_id="046d",
                product_id="c24f",
                event_node=None,
                sysfs_path=Path(directory),
                attributes={"alternate_modes": path},
            )
            with self.assertRaises(ValueError):
                device.switch_mode("unknown")


if __name__ == "__main__":
    unittest.main()
