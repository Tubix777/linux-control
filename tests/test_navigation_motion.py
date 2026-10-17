"""Visible navigation, interruption, picking and lifecycle in a private display."""
import tempfile
import time
import unittest
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Graphene, Gtk
from linux_control.app import CSS, MainWindow
from linux_control.settings import Settings


def pump(seconds=.03):
    deadline = time.monotonic() + seconds
    context = GLib.MainContext.default()
    while time.monotonic() < deadline:
        for _ in range(100):
            if not context.pending():
                break
            context.iteration(False)
        time.sleep(.002)


def wait_for(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        pump(.01)
    if not predicate():
        raise AssertionError("Navigation did not settle")


class EditablePage(Gtk.Box):
    def __init__(self, host, translator, settings):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.entry = Gtk.Entry(text="Unsaved profile")
        self.card = Gtk.Box(css_classes=["card"])
        self.card.append(self.entry)
        self.append(self.card)
        self.active = False
        self.closed = False

    def set_active(self, active):
        self.active = active

    def sync_motion(self):
        pass

    def close(self):
        self.closed = True


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default(), "Private GTK display required")
class NavigationMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()
        cls.app = Adw.Application(application_id="io.github.Tubix777.NavigationMotionTests",
                                  flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)
        cls.provider = Gtk.CssProvider()
        cls.provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), cls.provider, 620)

    @classmethod
    def tearDownClass(cls):
        Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(), cls.provider)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.desktop = Gtk.Settings.get_default()
        self.previous = self.desktop.get_property("gtk-enable-animations")
        self.desktop.set_property("gtk-enable-animations", True)
        self.window = MainWindow(self.app, Settings(Path(self.temp.name) / "preferences.json"),
                                  {name: EditablePage for name in ("hardware", "wheel", "doctor")})
        self.window.present()
        wait_for(lambda: self.window.page_transition.get_width() > 100)
        pump(.6)
        self.deck = self.window.page_transition

    def tearDown(self):
        self.window.on_close()
        self.window.destroy()
        self.desktop.set_property("gtk-enable-animations", self.previous)
        pump()
        self.temp.cleanup()

    def test_blend_has_intermediate_frames_and_does_not_double_fade_controls(self):
        self.window.select_page("doctor")
        self.assertIsNotNone(self.deck._tick_id)
        self.assertIsNotNone(self.deck._picture)
        self.assertEqual(self.window.pages["doctor"].card.get_opacity(), 1)
        self.assertEqual(self.window.stack.get_transition_type(), Gtk.StackTransitionType.NONE)
        samples = []
        while self.deck._tick_id is not None:
            samples.append(self.deck._progress)
            pump(.02)
        self.assertGreater(len({round(value, 2) for value in samples}), 4)
        self.assertTrue(all(a <= b for a, b in zip(samples, samples[1:])))
        self.assertEqual(self.deck._offset, (0, 0))
        self.assertIsNone(self.deck._picture)
        self.assertIsNone(self.window.motion._tick_id)

    def test_rapid_changes_use_latest_target_preserve_values_and_finish(self):
        original = self.window.pages["wheel"]
        original.entry.set_text("Pending wheel profile")
        for name in ("wheel", "doctor", "hardware", "doctor", "wheel"):
            self.window.select_page(name)
            pump(.04)
        self.assertEqual(self.window.current_page, "wheel")
        self.assertIs(self.window.stack.get_visible_child(), original)
        self.assertEqual(original.entry.get_text(), "Pending wheel profile")
        self.assertEqual(sum(page.active for page in self.window.pages.values()), 1)
        wait_for(lambda: self.deck._tick_id is None)
        self.assertIsNone(self.deck._picture)
        self.assertIsNone(self.window.selection_indicator._tick_id)

    def test_input_picking_follows_the_transformed_page(self):
        self.window.select_page("wheel")
        pump(.05)
        entry = self.window.pages["wheel"].entry
        okay, bounds = entry.compute_bounds(self.deck)
        self.assertTrue(okay)
        picked = self.deck.pick(bounds.get_x() + bounds.get_width() / 2,
                                bounds.get_y() + bounds.get_height() / 2, Gtk.PickFlags.DEFAULT)
        self.assertTrue(picked is entry or picked.is_ancestor(entry))
        entry.set_text("Still interactive during motion")
        self.assertEqual(entry.get_text(), "Still interactive during motion")

    def painted_bytes(self):
        snapshot = Gtk.Snapshot()
        self.deck.do_snapshot(snapshot)
        rectangle = Graphene.Rect()
        rectangle.init(0, 0, self.deck.get_width(), self.deck.get_height())
        texture = self.window.get_renderer().render_texture(snapshot.to_node(), rectangle)
        return bytes(texture.save_to_png_bytes().get_data())

    def test_first_frame_and_interruption_preserve_the_displayed_pixels(self):
        before = self.painted_bytes()
        self.window.select_page("doctor")
        self.assertEqual(self.painted_bytes(), before)
        pump(.12)
        self.assertTrue(0 < self.deck._progress < 1)
        middle = self.painted_bytes()
        self.window.select_page("wheel")
        self.assertEqual(self.painted_bytes(), middle)

    def test_same_page_and_invalid_navigation_do_not_restart_animation(self):
        self.window.select_page("wheel")
        callback = self.deck._tick_id
        self.window.select_page("wheel")
        self.window.select_page("unknown")
        self.assertEqual(self.deck._tick_id, callback)
        self.assertFalse(self.deck.navigate("unknown"))

    def test_download_return_and_language_keep_state(self):
        self.window.select_page("doctor")
        self.window.select_downloads("doctor")
        pump(.06)
        self.assertEqual(self.deck._direction, (1, 0))
        self.window.language.set_selected(1)
        self.window.select_page("doctor")
        self.assertEqual(self.deck._direction, (-1, 0))
        wait_for(lambda: self.deck._tick_id is None)
        self.assertEqual(self.window.page_title.get_label(), "Diagnostics")
        self.assertEqual(self.window.pages["doctor"].entry.get_text(), "Unsaved profile")

    def test_motion_reduction_settles_in_flight_transition_and_indicator(self):
        self.window.select_page("doctor")
        pump(.08)
        self.window.motion_switch.set_active(True)
        self.assertIsNone(self.deck._tick_id)
        self.assertIsNone(self.deck._picture)
        self.assertEqual(self.deck._offset, (0, 0))
        self.assertIsNone(self.window.selection_indicator._tick_id)
        self.window.select_page("wheel")
        self.assertIsNone(self.deck._tick_id)
        self.assertEqual(self.window.stack.get_visible_child_name(), "wheel")

    def test_resizing_and_unmapping_discard_old_picture(self):
        self.window.select_page("doctor")
        self.window.set_default_size(1000, 700)
        wait_for(lambda: self.window.get_width() <= 1050)
        self.assertIsNone(self.deck._picture)
        self.window.select_page("wheel")
        self.window.set_visible(False)
        self.assertIsNone(self.deck._tick_id)
        self.assertIsNone(self.deck._picture)
        self.window.present()
        pump(.1)
        self.assertEqual(self.deck._offset, (0, 0))

    def test_close_discards_all_navigation_callbacks(self):
        self.window.select_page("doctor")
        pump(.05)
        self.window.on_close()
        self.assertIsNone(self.deck._tick_id)
        self.assertIsNone(self.deck._picture)
        self.assertIsNone(self.window.selection_indicator._tick_id)
        self.assertFalse(self.deck.navigate("hardware"))
