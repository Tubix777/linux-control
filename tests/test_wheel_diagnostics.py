import tempfile
import unittest
from pathlib import Path

from wheel_control.diagnostics import build_diagnostics, diagnostics_json
from wheel_control.model import WheelDevice


class DiagnosticsTests(unittest.TestCase):
    def test_report_contains_capabilities_without_serial_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attribute = Path(directory) / "range"
            attribute.write_text("900\n", encoding="utf-8")
            device = WheelDevice(
                name="Test Wheel",
                vendor_id="046d",
                product_id="c24f",
                event_node=None,
                sysfs_path=Path(directory),
                firmware_revision="8900",
                attributes={"range": attribute},
                ff_capabilities={"gain"},
                axis_ranges={0x00: (0, 65535), 0x09: (0, 255)},
            )
            report = build_diagnostics([device])
            result = report["devices"][0]
            self.assertEqual(result["usb_id"], "046d:c24f")
            self.assertEqual(result["attributes"]["range"]["value"], "900")
            self.assertEqual(result["force_feedback_controls"], ["gain"])
            self.assertEqual(result["firmware_revision"], "8900")
            self.assertEqual(result["input_axes"][0]["name"], "X")
            self.assertEqual(result["input_axes"][1]["name"], "GAS")
            self.assertNotIn("serial", diagnostics_json([device]).casefold())

    def test_ps4_mode_has_actionable_recommendation(self) -> None:
        device = WheelDevice(
            name="Logitech G29 (PS4 mode)",
            vendor_id="046d",
            product_id="c260",
            event_node=None,
            sysfs_path=None,
        )
        result = build_diagnostics([device])["devices"][0]
        codes = {item["code"] for item in result["recommendations"]}
        self.assertIn("g29-ps4-mode", codes)
        self.assertIn("no-controls", codes)


if __name__ == "__main__":
    unittest.main()
