"""Finite interaction animation lifecycle checks in the private GTK display."""
import tempfile
import time
import unittest
from pathlib import Path

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from linux_control.app import CSS, MainWindow
from linux_control.interactions import MotionController
from linux_control.settings import Settings
from test_shell import FakePage


def pump_until(predicate, timeout=2):
    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for _ in range(100):
            if not context.pending():
                break
            context.iteration(False)
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("Animation did not settle")


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default() is not None,
                     "GTK display unavailable")
class MotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()

    def setUp(self):
        self.desktop = Gtk.Settings.get_default()
        self.previous = self.desktop.get_property("gtk-enable-animations")
        self.desktop.set_property("gtk-enable-animations", True)
        self.window = Gtk.Window(default_width=500, default_height=400)
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.card.add_css_class("card")
        self.entry = Gtk.Entry(text="unsaved profile")
        self.expander = Gtk.Expander(label="Details")
        self.expander.set_child(self.entry)
        self.card.append(self.expander)
        self.root.append(self.card)
        self.window.set_child(self.root)
        self.motion = MotionController(self.window)
        self.motion.decorate(self.root)

    def tearDown(self):
        self.motion.close()
        self.window.destroy()
        self.desktop.set_property("gtk-enable-animations", self.previous)

    def show(self):
        self.window.present()
        pump_until(lambda: self.window.get_mapped() and self.card.get_height() > 0)

    def test_expansion_and_collapse_preserve_unsaved_values(self):
        reveal = self.expander.get_next_sibling()
        self.assertIsInstance(reveal, Gtk.Revealer)
        self.assertIs(reveal.get_child(), self.entry)
        self.motion.decorate(self.root)
        self.assertIs(reveal, self.expander.get_next_sibling())
        self.show()
        self.expander.emit("activate")
        self.assertTrue(self.expander.get_expanded())
        pump_until(lambda: reveal.get_child_revealed())
        self.expander.emit("activate")
        self.assertFalse(self.expander.get_expanded())
        pump_until(lambda: not reveal.get_child_revealed())
        self.assertEqual(self.entry.get_text(), "unsaved profile")
        self.motion.set_enabled(False)
        self.expander.set_expanded(True)
        self.assertTrue(reveal.get_reveal_child())
        self.assertEqual(reveal.get_transition_duration(), 0)

    def test_card_entrance_runs_then_releases_its_frame_callback(self):
        self.show()
        self.assertIsNotNone(self.motion._tick_id)
        self.assertLess(self.card.get_opacity(), 1)
        pump_until(lambda: self.motion._tick_id is None)
        self.assertEqual(self.card.get_opacity(), 1)
        self.assertEqual(self.motion._fades, {})

    def test_reduction_and_close_cancel_in_flight_motion(self):
        self.show()
        self.expander.set_expanded(True)
        self.motion.set_enabled(False)
        reveal = self.expander.get_next_sibling()
        pump_until(lambda: reveal.get_child_revealed())
        self.assertIsNone(self.motion._tick_id)
        self.assertEqual(self.card.get_opacity(), 1)
        self.motion.close()
        self.motion.close()
        self.assertEqual(len(self.motion._handlers), 0)

    def test_diagnostic_cards_keep_their_existing_animation_owner(self):
        result = Gtk.Box()
        result.add_css_class("card")
        result.add_css_class("scan-result")
        result.set_opacity(0)
        self.root.append(result)
        self.motion.decorate(result)
        self.motion.set_enabled(False)
        self.show()
        self.assertEqual(result.get_opacity(), 0)
        self.assertNotIn(result, self.motion._fades)

    def test_stylesheet_parses_without_warnings(self):
        errors = []
        provider = Gtk.CssProvider()
        provider.connect("parsing-error", lambda _p, _section, error: errors.append(str(error)))
        provider.load_from_string(CSS)
        self.assertEqual(errors, [])

    def test_replacing_dynamic_results_releases_old_widget_handlers(self):
        reveal = self.expander.get_next_sibling()
        self.assertIn(self.expander, self.motion._reveals)
        self.motion.forget(self.root)
        self.assertEqual(self.motion._reveals, {})
        self.assertEqual(self.motion._handlers, {})
        self.expander.set_expanded(True)
        self.assertFalse(reveal.get_reveal_child())

    def test_desktop_motion_change_updates_all_pages_immediately(self):
        app = Adw.Application(application_id="io.github.Tubix777.MotionTests",
                              flags=Gio.ApplicationFlags.NON_UNIQUE)
        app.register(None)
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(Path(directory) / "preferences.json")
            window = MainWindow(app, settings,
                                {name: FakePage for name in ("hardware", "wheel", "doctor")})
            try:
                self.desktop.set_property("gtk-enable-animations", False)
                self.assertFalse(window.motion.enabled)
                self.assertTrue(window.has_css_class("reduce-motion"))
                self.assertEqual(window.stack.get_transition_duration(), 0)
                self.assertFalse(settings.reduced_motion)
                self.desktop.set_property("gtk-enable-animations", True)
                self.assertTrue(window.motion.enabled)
                self.assertFalse(window.has_css_class("reduce-motion"))
                window.motion_switch.set_active(True)
                self.desktop.set_property("gtk-enable-animations", False)
                self.desktop.set_property("gtk-enable-animations", True)
                self.assertFalse(window.motion.enabled)
                self.assertEqual(window.current_page, "hardware")
            finally:
                window.on_close()
                window.destroy()
