"""Safety boundaries, faithful exports and embedded-page lifecycle."""
import csv
import io
import json
from pathlib import Path
from types import SimpleNamespace
import stat
import unittest
from unittest.mock import Mock, patch

from linux_control.pages.hardware import (
    HardwarePage, csv_text, diagnostic_text, fan_command, percent, safe_helper,
)
from gi.repository import Adw, Gdk, Gtk


class FanCommandTests(unittest.TestCase):
    def setUp(self):
        self.safe = patch("linux_control.pages.hardware.safe_helper", return_value=True).start()
        self.which = patch("linux_control.pages.hardware.shutil.which", return_value="/usr/bin/pkexec").start()
        self.channels = patch("linux_control.pages.hardware.channels", return_value=[{"channel": 1}]).start()
        self.addCleanup(patch.stopall)
        self.curve = [[30, 60], [45, 70], [60, 85], [75, 100], [85, 100]]

    def test_curve_uses_original_helper_with_exact_payload(self):
        args = fan_command(1, "curve", self.curve)
        self.assertEqual(args[:4], ["/usr/bin/pkexec", "/usr/libexec/anvil-fan-helper", "1", "curve"])
        self.assertEqual(json.loads(args[4]), self.curve)

    def test_missing_helper_disables_command(self):
        self.safe.return_value = False
        with self.assertRaises(ValueError):
            fan_command(1, "full")

    def test_channel_is_revalidated_at_command_time(self):
        self.channels.return_value = []
        with self.assertRaises(ValueError):
            fan_command(1, "full")

    def test_monitor_only_never_reaches_channel_probe(self):
        with self.assertRaises(ValueError):
            fan_command(1, "full", monitor_only=True)
        self.channels.assert_not_called()

    def test_boolean_and_unknown_action_are_rejected(self):
        for channel, action in ((True, "full"), ("1", "full"), (1, "shell")):
            with self.subTest(channel=channel, action=action), self.assertRaises(ValueError):
                fan_command(channel, action)

    def test_curve_limits_match_packaged_helper(self):
        bad_curves = [
            [[30, 60], [45, 70], [60, 85], [75, 99], [85, 100]],
            [[30, 60], [45, 70], [60, 85], [75, 100], [86, 100]],
            [[30, 49], [45, 70], [60, 85], [75, 100], [85, 100]],
            [[30, 60], [30, 70], [60, 85], [75, 100], [85, 100]],
            [[30, 70], [45, 60], [60, 85], [75, 100], [85, 100]],
            [[30, 60], [45, 70], [60, 85], [75, 100], [85, True]],
        ]
        for curve in bad_curves:
            with self.subTest(curve=curve), self.assertRaises(ValueError):
                fan_command(1, "curve", curve)

    def test_full_and_restore_have_no_untrusted_extra_payload(self):
        self.assertEqual(len(fan_command(1, "full")), 4)
        self.assertEqual(len(fan_command(1, "restore")), 4)


class HelperTrustTests(unittest.TestCase):
    def candidate(self, owner=0, mode=stat.S_IFREG | 0o755, parent_mode=stat.S_IFDIR | 0o755):
        path = Mock()
        path.is_symlink.return_value = False
        path.stat.return_value = SimpleNamespace(st_uid=owner, st_mode=mode)
        parent = Mock()
        parent.stat.return_value = SimpleNamespace(st_uid=0, st_mode=parent_mode)
        path.parents = [parent]
        return path

    def test_root_owned_executable_in_root_owned_path(self):
        self.assertTrue(safe_helper(self.candidate()))

    def test_user_owned_or_writable_helper_is_rejected(self):
        self.assertFalse(safe_helper(self.candidate(owner=1000)))
        self.assertFalse(safe_helper(self.candidate(mode=stat.S_IFREG | 0o775)))
        self.assertFalse(safe_helper(self.candidate(mode=stat.S_IFREG | 0o644)))

    def test_symlink_and_writable_parent_are_rejected(self):
        path = self.candidate()
        path.is_symlink.return_value = True
        self.assertFalse(safe_helper(path))
        self.assertFalse(safe_helper(self.candidate(parent_mode=stat.S_IFDIR | 0o777)))

    def test_missing_file_is_unavailable(self):
        path = self.candidate()
        path.stat.side_effect = FileNotFoundError()
        self.assertFalse(safe_helper(path))


class ExportTests(unittest.TestCase):
    def test_csv_preserves_unknown_fields_and_real_zero(self):
        contents = csv_text([{"time": 1, "cpu_usage": 0, "cpu_temp": None, "gpu": None}])
        row = next(csv.DictReader(io.StringIO(contents)))
        self.assertEqual(row["cpu_usage"], "0")
        self.assertEqual(row["cpu_temp"], "")
        self.assertEqual(row["gpu_usage"], "")

    def test_diagnostics_export_only_selected_identity_fields(self):
        text = diagnostic_text({"cpu": "Processor", "serial": "private-serial", "pci": "sensitive-debug"},
                               {"sensors": [{"chip": "coretemp", "label": "Package", "value": 42,
                                             "unit": "°C", "path": "/sys/private-path"}]}, [])
        self.assertNotIn("private-serial", text)
        self.assertNotIn("sensitive-debug", text)
        self.assertNotIn("/sys/private-path", text)
        self.assertEqual(json.loads(text)["sensors"][0]["value"], 42)

    def test_percentage_does_not_invent_missing_totals(self):
        self.assertIsNone(percent(None, 100))
        self.assertIsNone(percent(10, 0))
        self.assertIsNone(percent(float("nan"), 100))
        self.assertIsNone(percent(10, float("inf")))
        self.assertEqual(percent(25, 100), 25)


class TranslatorStub:
    def __call__(self, source, **values):
        return source.format(**values) if values else source
    def bind(self, widget, source, setter="set_label"):
        getattr(widget, setter)(source)
    def connect(self, callback):
        pass


@unittest.skipUnless(Gdk.Display.get_default() is not None, "GTK display required")
class PageLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Gtk.init()
        Adw.init()

    def setUp(self):
        self.page = HardwarePage(Gtk.Window(), TranslatorStub(), SimpleNamespace(reduced_motion=True))
        self.addCleanup(self.page.close)

    def sample(self):
        return {"time": 1, "cpu_usage": 0, "cpu_temp": None, "cpu_mhz": None,
                "memory_used": 10, "memory_total": 100, "disk_used": 25, "disk_total": 100,
                "sensors": [], "gpu": None, "profiles": [], "profile": None}

    def test_construction_never_mutates_hardware(self):
        with patch("linux_control.pages.hardware.execute") as command, patch("linux_control.pages.hardware.set_profile") as profile:
            self.page._active = True
            self.page._received({"cpu": "Test CPU"}, self.sample(), [], False)
            command.assert_not_called()
            profile.assert_not_called()
            self.assertFalse(self.page.profile_apply.get_sensitive())
            self.assertFalse(self.page.rgb_apply.get_sensitive())

    def test_closed_page_rejects_late_worker_result(self):
        self.page._active = True
        self.page.close()
        self.page._received({}, self.sample(), [], False)
        self.assertFalse(self.page._history)

    def test_sample_started_before_write_cannot_enable_controls(self):
        self.page._active = True
        self.page._generation = 2
        with patch.object(self.page, "_request_sample") as refresh:
            self.page._received({}, self.sample(), [{"channel": 1}], False, generation=1)
            self.assertEqual(self.page._last_fan_success, 0)
            self.assertFalse(self.page._history)
            refresh.assert_called_once()

    def test_pause_disables_all_mutation_controls(self):
        self.page._active = True
        self.page._received({}, self.sample(), [], False)
        self.page._toggle_pause()
        self.assertFalse(self.page.profile_apply.get_sensitive())
        self.assertFalse(self.page.rgb_apply.get_sensitive())
        self.assertTrue(self.page._paused)

    def test_language_refresh_preserves_unapplied_control_choices(self):
        self.page._active = True
        sample = self.sample()
        sample.update(profile="balanced", profiles=[{"Profile": {"data": "balanced"}},
                                                   {"Profile": {"data": "performance"}}])
        self.page._received({}, sample, [], False)
        self.page.profile_selector.set_selected(1)
        self.page.preset_selector.set_selected(2)
        self.page.retranslate()
        self.assertEqual(self.page.profile_selector.get_selected(), 1)
        self.assertEqual(self.page.preset_selector.get_selected(), 2)

    def test_reduced_motion_stops_pending_metric_animation(self):
        self.page._active = True
        self.page._targets = {"cpu": 50, "gpu": None, "memory": 20, "disk": 25}
        self.page.sync_motion()
        self.assertEqual(self.page._motion, 0)
        self.assertEqual(self.page.metrics["cpu"][0].get_label(), "50%")


if __name__ == "__main__":
    unittest.main()
