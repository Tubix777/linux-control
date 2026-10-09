"""Embedded wheel integration: lifecycle, host ownership and explicit writes."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from linux_control.i18n import Translator
from linux_control.pages.wheel import WheelPage
from linux_control.settings import Settings
from wheel_control.model import WheelDevice, demo_g29
from wheel_control.profiles import ProfileStore, WheelProfile
from wheel_control.telemetry import Telemetry


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default() is not None, "GTK display unavailable")
class WheelPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        directory = Path(self.temporary.name)
        self.preferences = Settings(directory / "preferences.json")
        self.translator = Translator("en")
        self.profile_store = ProfileStore(directory / "profiles.json")
        self.monitor = MagicMock()
        self.patches = [
            patch("linux_control.pages.wheel.DeviceMonitor", return_value=self.monitor),
            patch("linux_control.pages.wheel.ProfileStore", return_value=self.profile_store),
            patch("linux_control.pages.wheel.discover_wheels", return_value=[]),
        ]
        for patcher in self.patches:
            patcher.start()
        self.host = Adw.Window()
        self.page = WheelPage(self.host, self.translator, self.preferences)
        self.host.set_content(self.page)
        self.drain(lambda: not self.page._scan_running and not self.page._refresh_source)

    def tearDown(self):
        self.page.close()
        self.host.destroy()
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temporary.cleanup()

    def drain(self, done, timeout=2):
        deadline = time.monotonic() + timeout
        context = GLib.MainContext.default()
        while time.monotonic() < deadline:
            while context.pending():
                context.iteration(False)
            if done():
                return
            time.sleep(0.005)
        self.fail("GTK callback did not finish")

    def demo(self):
        self.page._load_devices([self.page._demo_device])
        self.drain(lambda: not self.page._device_loading)
        return self.page._demo_device

    def test_page_uses_common_window_and_starts_without_demo(self):
        self.assertIsInstance(self.page, Gtk.Box)
        self.assertNotIsInstance(self.page, Gtk.Window)
        self.assertIs(self.page._dialog_parent(), self.host)
        self.assertEqual(self.page.stack.get_visible_child_name(), "empty")
        self.assertIsNone(self.page.current_device)
        self.monitor.start.assert_called_once()

    def test_discovery_and_profile_loading_never_write_device(self):
        device = self.demo()
        self.page.profiles = [WheelProfile("Rally", rotation_range=540, gain=45)]
        self.page.profile_model.append("Rally")
        self.page.profile_dropdown.set_selected(0)
        self.page._load_profile(None)
        self.assertEqual(self.page.range_control.get_value(), 540)
        self.assertEqual(self.page.gain_control.get_value(), 45)
        self.assertEqual(device._demo_values, {})
        self.assertEqual(self.page._applied_range, 900)

    def test_apply_is_explicit_and_keeps_live_angle_on_applied_range(self):
        device = self.demo()
        self.page.range_control.set_value(540)
        self.assertEqual(device._demo_values, {})
        self.page._apply_settings(None)
        self.drain(lambda: not self.page._write_running)
        self.assertEqual(device._demo_values["range"], 540)
        self.assertEqual(self.page._applied_range, 540)
        self.page._update_telemetry(Telemetry(steering=1))
        self.assertEqual(self.page.angle_label.get_label(), "+270°")

    def test_language_switch_preserves_unsaved_controls_and_selection(self):
        device = self.demo()
        self.page.range_control.set_value(450)
        self.page.gain_control.set_value(35)
        self.translator.set_language("tr")
        self.translator.set_language("en")
        self.assertIs(self.page.current_device, device)
        self.assertEqual(self.page.range_control.get_value(), 450)
        self.assertEqual(self.page.gain_control.get_value(), 35)
        self.assertEqual(device._demo_values, {})

    def test_telemetry_from_previous_device_is_ignored(self):
        self.demo()
        self.page._active = True
        generation = self.page._device_generation
        self.page._telemetry_from_thread(Telemetry(steering=0.8), generation - 1)
        self.page._flush_telemetry()
        self.assertEqual(self.page.gauge.steering, 0)
        self.page._telemetry_from_thread(Telemetry(steering=0.6), generation)
        self.page._flush_telemetry()
        self.assertEqual(self.page.gauge.steering, 0.6)

    def test_hidden_page_pauses_demo_and_reduced_motion_keeps_live_input(self):
        self.demo()
        self.assertEqual(self.page._demo_source, 0)
        self.page.set_active(True)
        self.assertGreater(self.page._demo_source, 0)
        self.page.set_active(False)
        self.assertEqual(self.page._demo_source, 0)
        self.preferences.reduced_motion = True
        self.page.sync_motion()
        self.assertEqual(self.page.stack.get_transition_duration(), 0)
        self.page._update_telemetry(Telemetry(steering=0.3))
        self.assertEqual(self.page.gauge.steering, 0.3)

    def test_export_dialog_is_parented_to_host(self):
        self.demo()
        dialog = MagicMock()
        with patch.object(self.page, "_file_dialog", return_value=dialog):
            self.page._export_profile(None)
        self.assertIs(dialog.save.call_args.args[0], self.host)

    def test_close_is_idempotent_and_stale_callbacks_are_inert(self):
        self.demo()
        self.page.set_active(True)
        old_generation = self.page._scan_generation
        self.page.close()
        self.page.close()
        self.monitor.stop.assert_called_once()
        for field in ("_refresh_source", "_ffb_source", "_demo_source",
                      "_telemetry_source"):
            self.assertEqual(getattr(self.page, field), 0)
        self.page._scan_finished(old_generation, [], None)
        self.assertIsNotNone(self.page.current_device)
        self.page._telemetry_from_thread(Telemetry(steering=1), 0)
        self.assertIsNone(self.page._pending_telemetry)

    def test_device_settings_reads_and_apply_writes_run_off_main_thread(self):
        main_thread = threading.get_ident()
        read_threads, write_threads = [], []
        original_read = WheelDevice.read_attribute
        original_write = WheelDevice.write_attribute

        def read(device, name, default=0):
            read_threads.append(threading.get_ident())
            return original_read(device, name, default)

        def write(device, name, value):
            write_threads.append(threading.get_ident())
            return original_write(device, name, value)

        with patch.object(WheelDevice, "read_attribute", read), patch.object(WheelDevice, "write_attribute", write):
            self.demo()
            self.page._apply_settings(None)
            self.drain(lambda: not self.page._write_running)
        self.assertTrue(read_threads)
        self.assertTrue(write_threads)
        self.assertNotIn(main_thread, read_threads)
        self.assertNotIn(main_thread, write_threads)

    def test_late_apply_callback_cannot_update_replacement_selection(self):
        device = self.demo()
        old_generation = self.page._device_generation
        self.page._select_device(None)
        self.page._write_running = True
        self.page._apply_finished(old_generation, device, {"range": 450}, ["range"], [])
        self.assertEqual(self.page._applied_range, 900)
        self.assertIsNone(self.page.current_device)
        self.assertFalse(self.page.apply_button.get_sensitive())

    def test_rapid_device_changes_coalesce_to_latest_selection(self):
        first, second, third = demo_g29(), demo_g29(), demo_g29()
        started, released = threading.Event(), threading.Event()
        read_devices = []
        original_read = WheelDevice.read_attribute

        def read(device, name, default=0):
            read_devices.append(device)
            if device is first and name == "range":
                started.set()
                released.wait(1)
            return original_read(device, name, default)

        with patch.object(WheelDevice, "read_attribute", read):
            self.page._select_device(first)
            self.assertTrue(started.wait(0.5))
            self.page._select_device(second)
            self.page._select_device(third)
            released.set()
            self.drain(lambda: self.page.current_device is third)
        self.assertFalse(any(item is second for item in read_devices))
        self.assertTrue(any(item is third for item in read_devices))


if __name__ == "__main__":
    unittest.main()
