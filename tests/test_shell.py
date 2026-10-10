"""Navigation, live preferences and lifecycle without hardware access."""
import tempfile
import unittest
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk
from linux_control.settings import Settings
from linux_control.app import MainWindow


class SettingsTests(unittest.TestCase):
    def test_preferences_round_trip_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preferences.json"
            settings = Settings(path)
            settings.language, settings.reduced_motion = "en", True
            settings.save()
            loaded = Settings(path)
            self.assertEqual(loaded.language, "en")
            self.assertTrue(loaded.reduced_motion)
            path.write_text('{"language":"unknown", "reduced_motion":"yes"}')
            invalid = Settings(path)
            self.assertEqual(invalid.language, "tr")
            self.assertFalse(invalid.reduced_motion)
            path.write_text('[]')
            self.assertEqual(Settings(path).language, "tr")


class FakePage(Gtk.Box):
    def __init__(self, host, translator, settings):
        super().__init__()
        self.host = host
        self.activations = []
        self.closed = 0
        self.motion_syncs = 0

    def set_active(self, active):
        self.activations.append(active)

    def sync_motion(self):
        self.motion_syncs += 1

    def close(self):
        self.closed += 1


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default() is not None, "GTK display unavailable; run in virtual compositor")
class ShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()
        cls.app = Adw.Application(application_id="io.github.Tubix777.LinuxControl.ShellTests", flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Settings(Path(self.temp.name) / "prefs.json")
        self.window = MainWindow(self.app, self.settings, {name: FakePage for name in ("hardware", "wheel", "doctor")})

    def tearDown(self):
        self.window.on_close()
        self.window.destroy()
        self.temp.cleanup()

    def test_navigation_keeps_one_host_and_deactivates_previous(self):
        self.window.select_page("wheel")
        self.assertEqual(self.window.current_page, "wheel")
        self.assertEqual(self.window.stack.get_visible_child_name(), "wheel")
        self.assertFalse(self.window.pages["hardware"].activations[-1])
        self.assertTrue(self.window.pages["wheel"].activations[-1])
        self.assertTrue(all(page.host is self.window for page in self.window.pages.values()))
        self.assertTrue(self.window.nav_buttons["wheel"].has_css_class("selected"))
        self.assertFalse(self.window.nav_buttons["hardware"].has_css_class("selected"))

    def test_language_switch_preserves_pages_and_selection_and_persists(self):
        self.window.select_page("doctor")
        pages = dict(self.window.pages)
        self.window.language.set_selected(1)
        self.assertEqual(self.window.pages, pages)
        self.assertEqual(self.window.current_page, "doctor")
        self.assertEqual(self.window.page_title.get_label(), "Diagnostics")
        self.assertEqual(Settings(self.settings.path).language, "en")

    def test_reduced_motion_applies_to_all_modules_without_navigation(self):
        before = {name: page.motion_syncs for name, page in self.window.pages.items()}
        self.window.motion_switch.set_active(True)
        self.assertEqual(self.window.stack.get_transition_duration(), 0)
        self.assertTrue(all(page.motion_syncs == before[name] + 1 for name, page in self.window.pages.items()))
        self.assertTrue(Settings(self.settings.path).reduced_motion)
        self.assertEqual(self.window.current_page, "hardware")

    def test_close_is_idempotent_and_late_navigation_is_ignored(self):
        self.window.on_close()
        self.window.on_close()
        self.window.select_page("wheel")
        self.assertTrue(all(page.closed == 1 for page in self.window.pages.values()))
        self.assertEqual(self.window.current_page, "hardware")
