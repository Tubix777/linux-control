"""Actual three-page window: asynchronous navigation, state and layout."""
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from doctor.core import Finding
from linux_control.app import CSS, MainWindow
from linux_control.settings import Settings
from wheel_control.model import demo_g29
from wheel_control.profiles import ProfileStore


def sample():
    return {"time": time.time(), "cpu_usage": 25, "cpu_temp": 42, "cpu_mhz": 3200,
            "memory_used": 4 * 2**30, "memory_total": 16 * 2**30,
            "disk_used": 100 * 2**30, "disk_total": 1000 * 2**30,
            "sensors": [], "gpu": {"name": "Test GPU", "usage": 30, "temperature": 45},
            "profile": "balanced", "profiles": [{"Profile": {"data": "balanced"}},
                                                  {"Profile": {"data": "performance"}}]}


class ReadOnlyMonitor:
    identity = {"cpu": "Test Processor", "board": "Test Board", "os": "Linux"}

    def sample(self):
        return sample()


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default() is not None, "GTK display required; use a private virtual compositor")
class ActualWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        cls.app = Adw.Application(application_id="io.github.Tubix777.LinuxControl.IntegrationTests",
                                  flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)
        cls.provider = Gtk.CssProvider()
        cls.provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), cls.provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 20)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        directory = Path(self.temp.name)
        self.preferences = Settings(directory / "preferences.json")
        self.preferences.reduced_motion = True
        self.device = demo_g29()
        self.monitor = MagicMock()
        self.patches = [
            patch("linux_control.pages.hardware.Monitor", ReadOnlyMonitor),
            patch("linux_control.pages.hardware.channels", return_value=[]),
            patch("linux_control.pages.hardware.safe_helper", return_value=False),
            patch("linux_control.pages.wheel.DeviceMonitor", return_value=self.monitor),
            patch("linux_control.pages.wheel.discover_wheels", return_value=[self.device]),
            patch("linux_control.pages.wheel.ProfileStore", return_value=ProfileStore(directory / "profiles.json")),
            patch("linux_control.pages.doctor.list_flatpaks", return_value=[
                ("org.mozilla.firefox", "Firefox", "user"),
                ("org.gnome.Calculator", "Calculator", "system"),
            ]),
        ]
        for patcher in self.patches:
            patcher.start()
        self.window = MainWindow(self.app, self.preferences, initial="doctor")
        self.window.present()
        self.drain(lambda: len(self.window.pages["doctor"].apps) == 2
                   and self.window.pages["wheel"].current_device is self.device)

    def tearDown(self):
        self.window.on_close()
        self.window.destroy()
        for patcher in reversed(self.patches):
            patcher.stop()
        self.temp.cleanup()

    def drain(self, done, timeout=3):
        deadline = time.monotonic() + timeout
        context = GLib.MainContext.default()
        while time.monotonic() < deadline:
            while context.pending():
                context.iteration(False)
            if done():
                return
            time.sleep(.004)
        self.fail("Native window did not reach the expected state")

    def settle(self, duration=.08):
        deadline = time.monotonic() + duration
        self.drain(lambda: time.monotonic() >= deadline)

    def test_actual_pages_share_one_host_and_remain_alive_during_navigation(self):
        pages = dict(self.window.pages)
        for name in ("hardware", "wheel", "doctor", "hardware"):
            self.window.select_page(name)
            self.assertEqual(self.window.stack.get_visible_child_name(), name)
            self.assertEqual(self.window.pages, pages)
            self.assertTrue(all(page.host is self.window for page in pages.values()))
            self.assertTrue(all(not page._closed for page in pages.values()))
            self.assertEqual(sum(page._active for page in pages.values()), 1)

    def test_download_navigation_preserves_real_unapplied_controls_and_app_selection(self):
        wheel, doctor = self.window.pages["wheel"], self.window.pages["doctor"]
        wheel.range_control.set_value(540)
        wheel.gain_control.set_value(42)
        doctor.dropdown.set_selected(1)
        for name in ("hardware", "wheel", "doctor"):
            self.window.select_downloads(name)
            self.assertFalse(any(page._active for page in self.window.pages.values()))
            self.window.language.set_selected(1)
            self.window.language.set_selected(0)
        self.window.select_page("wheel")
        self.assertEqual(wheel.range_control.get_value(), 540)
        self.assertEqual(wheel.gain_control.get_value(), 42)
        self.assertEqual(wheel.range_control.value_label.get_label(), "540°")
        self.assertEqual(wheel.gain_control.value_label.get_label(), "42%")
        self.assertEqual(doctor.dropdown.get_selected(), 1)
        self.assertEqual(self.device._demo_values, {})

    def test_attention_filter_retains_unknowns_and_restores_all_findings(self):
        doctor = self.window.pages["doctor"]
        findings = [Finding("Good", "ok", "Fine"), Finding("Warning", "warning", "Check"),
                    Finding("Unknown", "unknown", "Cannot read")]
        doctor.show_findings(findings)
        doctor.filter_button.set_active(True)
        self.assertEqual(len(doctor._cards), 2)
        self.assertEqual(doctor._findings, findings)
        self.assertFalse(doctor._auto_scroll)
        self.assertEqual(doctor.scan_counts["checks"].get_label(), "3")
        self.assertEqual(doctor.scan_counts["unknown"].get_label(), "1")
        doctor.filter_button.set_active(False)
        self.assertEqual(len(doctor._cards), 3)

    def test_scan_with_no_attention_findings_reveals_the_filtered_empty_state(self):
        doctor = self.window.pages["doctor"]
        findings = [Finding("Good", "ok", "Fine")]
        doctor.show_findings(findings)
        doctor.filter_button.set_active(True)
        doctor.show_findings(findings)
        self.drain(lambda: doctor._motion_tick_id is None)
        self.assertEqual(doctor._findings, findings)
        self.assertEqual(len(doctor._cards), 1)
        self.assertTrue(doctor._cards[0].has_css_class("doctor-empty"))
        self.assertEqual(doctor._cards[0].get_opacity(), 1)
        self.assertFalse(doctor._auto_scroll)

    def test_blocked_probes_do_not_block_navigation_or_gtk_callbacks(self):
        hardware_entered, doctor_entered, release = (threading.Event() for _ in range(3))
        threads = []
        def blocked_hardware(_monitor):
            threads.append(threading.get_ident())
            hardware_entered.set()
            release.wait(2)
            return sample()
        def blocked_scan():
            threads.append(threading.get_ident())
            doctor_entered.set()
            release.wait(2)
            return [Finding("Test result", "ok", "Read-only integration probe")]
        try:
            with patch.object(ReadOnlyMonitor, "sample", blocked_hardware), \
                    patch("linux_control.pages.doctor.scan", blocked_scan):
                self.window.select_page("hardware")
                self.assertTrue(hardware_entered.wait(.5))
                self.window.select_page("doctor")
                self.window.pages["doctor"].start_scan()
                self.assertTrue(doctor_entered.wait(.5))
                reached = []
                def switch():
                    self.window.select_page("wheel")
                    reached.append(self.window.current_page)
                    return GLib.SOURCE_REMOVE
                GLib.idle_add(switch)
                self.drain(lambda: reached == ["wheel"], timeout=.5)
                self.assertNotIn(threading.get_ident(), threads)
                self.assertFalse(release.is_set())
        finally:
            release.set()
            self.drain(lambda: not self.window.pages["doctor"]._busy
                       and not self.window.pages["hardware"]._polling)

    def test_language_change_preserves_every_unapplied_selection(self):
        hardware, wheel, doctor = (self.window.pages[name] for name in ("hardware", "wheel", "doctor"))
        self.window.select_page("hardware")
        self.drain(lambda: bool(hardware._sample))
        hardware.profile_selector.set_selected(1)
        hardware.preset_selector.set_selected(2)
        wheel.range_control.set_value(540)
        wheel.gain_control.set_value(42)
        doctor.dropdown.set_selected(1)
        doctor.folder = str(Path(self.temp.name) / "documents")
        pages = dict(self.window.pages)
        self.window.select_page("wheel")
        self.window.language.set_selected(1)
        self.assertEqual(self.window.pages, pages)
        self.assertEqual(self.window.current_page, "wheel")
        self.assertIn("simulated input", wheel.device_status.get_label())
        self.assertEqual(hardware.profile_selector.get_selected(), 1)
        self.assertEqual(hardware.preset_selector.get_selected(), 2)
        self.assertEqual(wheel.range_control.get_value(), 540)
        self.assertEqual(wheel.gain_control.get_value(), 42)
        self.assertEqual(wheel.range_control.value_label.get_label(), "540°")
        self.assertEqual(wheel.gain_control.value_label.get_label(), "42%")
        self.assertEqual(doctor.dropdown.get_selected(), 1)
        self.assertTrue(doctor.folder.endswith("documents"))
        self.assertEqual(self.device._demo_values, {})

    def test_doctor_scan_results_survive_navigation_and_language_switch(self):
        doctor = self.window.pages["doctor"]
        findings = [Finding("Sistem diski", "ok", "Test", metric=36, metric_label="Disk doluluğu")]
        with patch("linux_control.pages.doctor.scan", return_value=findings):
            doctor.start_scan()
            self.drain(lambda: not doctor._busy)
        self.window.select_page("wheel")
        self.window.language.set_selected(1)
        self.window.select_page("doctor")
        self.assertEqual(doctor._findings, findings)
        self.assertEqual(len(doctor._cards), 1)
        self.assertEqual(doctor._cards[0].get_opacity(), 1)

    def test_layout_has_no_horizontal_scroll_at_supported_window_sizes(self):
        for width, height in ((960, 620), (1280, 900)):
            # GTK's default size applies at first presentation. Recreate the
            # host rather than pretending set_default_size resizes a mapped one.
            self.window.on_close()
            self.window.destroy()
            self.window = MainWindow(self.app, self.preferences, initial="doctor")
            self.window.set_default_size(width, height)
            self.window.present()
            self.drain(lambda: self.window.get_width() > 0
                       and self.window.pages["wheel"].current_device is self.device)
            for name, view in ((name, view) for name in ("hardware", "wheel", "doctor")
                               for view in ("dashboard", "downloads")):
                self.window.select_page(name, view)
                self.settle()
                self.assertEqual(self.window.get_width(), width,
                                 f"{name}: minimum layout forced a wider window")
                self.assertEqual(self.window.pages["hardware"].metric_grid.get_max_children_per_line(),
                                 2 if width <= 1120 else 4)
                self.assertEqual(self.window.pages["wheel"].control_columns.get_orientation(),
                                 Gtk.Orientation.VERTICAL if width <= 1120 else Gtk.Orientation.HORIZONTAL)
                # Adwaita's minimum-sized client decoration adds two pixels.
                self.assertLessEqual(abs(self.window.get_height() - height), 2,
                                     f"{name}: minimum layout forced a taller window")
                page = (self.window.downloads if view == "downloads" else self.window.pages)[name]
                self.assertLessEqual(page.get_width(), self.window.get_width())
                self.assertGreater(page.get_width(), 500)
                for scrolled in self.scrollers(page):
                    adjustment = scrolled.get_hadjustment()
                    self.assertLessEqual(adjustment.get_upper() - adjustment.get_page_size(), 1,
                                         f"{name}: horizontal clipping at {width}×{height}")

    @staticmethod
    def scrollers(widget):
        result = [widget] if isinstance(widget, Gtk.ScrolledWindow) else []
        child = widget.get_first_child()
        while child:
            result.extend(ActualWindowTests.scrollers(child))
            child = child.get_next_sibling()
        return result

    def test_close_stops_real_page_sources_and_hotplug_monitor(self):
        self.window.select_page("hardware")
        self.drain(lambda: not self.window.pages["hardware"]._polling)
        self.window.select_page("wheel")
        self.assertGreater(self.window.pages["wheel"]._demo_source, 0)
        self.window.on_close()
        self.window.on_close()
        hardware, wheel, doctor = (self.window.pages[name] for name in ("hardware", "wheel", "doctor"))
        self.assertTrue(all(page._closed for page in (hardware, wheel, doctor)))
        self.assertEqual(hardware._source, 0)
        self.assertEqual(hardware._motion, 0)
        self.assertIsNone(doctor._motion_tick_id)
        for source in ("_refresh_source", "_ffb_source", "_demo_source", "_telemetry_source"):
            self.assertEqual(getattr(wheel, source), 0)
        self.monitor.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
