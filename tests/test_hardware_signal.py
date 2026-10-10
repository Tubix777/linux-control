"""Decorative motion follows fresh readings and owns no hardware writes."""
import unittest
from unittest.mock import patch

from gi.repository import Gdk, GLib, Gtk
from linux_control.motion import HardwareSignal


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default(), "GTK display required")
class SignalTests(unittest.TestCase):
    def setUp(self):
        self.enabled = True
        self.signal = HardwareSignal(lambda: self.enabled)
        self.window = Gtk.Window()
        self.window.set_child(self.signal)
        self.window.present()
        self.drain()

    def tearDown(self):
        self.signal.stop()
        self.window.destroy()
        self.drain()

    def drain(self):
        context = GLib.MainContext.default()
        while context.pending():
            context.iteration(False)

    def sample(self, *values):
        return {"sensors": [{"unit": "RPM", "value": v} for v in values]}

    def test_fan_rotation_does_not_invent_missing_or_zero_readings(self):
        for values in ((), (None,), (0,), (-2,), (True,), (float("nan"),)):
            with self.subTest(values=values):
                self.signal.readings(self.sample(*values))
                self.assertFalse(self.signal.spinning)
        self.signal.readings(self.sample(0, 900))
        self.assertTrue(self.signal.has_fan)
        self.assertTrue(self.signal.spinning)
        self.signal.readings({"sensors": None})
        self.assertFalse(self.signal.has_fan)

    def test_only_visible_active_fresh_enabled_signal_gets_frames(self):
        self.signal.readings(self.sample(850))
        self.assertEqual(self.signal._tick_id, 0)
        self.signal.active = True
        self.signal.sync()
        self.assertNotEqual(self.signal._tick_id, 0)
        self.enabled = False
        self.signal.sync()
        self.assertEqual(self.signal._tick_id, 0)
        self.enabled = True
        self.signal.sync()
        self.assertNotEqual(self.signal._tick_id, 0)
        self.window.set_visible(False)
        self.drain()
        self.assertEqual(self.signal._tick_id, 0)

    def test_stale_or_failed_sample_stops_motion(self):
        self.signal.active = True
        with patch("linux_control.motion.time.monotonic", return_value=100):
            self.signal.readings(self.sample(800))
            self.assertNotEqual(self.signal._tick_id, 0)
        with patch("linux_control.motion.time.monotonic", return_value=111):
            self.signal.sync()
            self.assertFalse(self.signal.fresh)
            self.assertEqual(self.signal._tick_id, 0)
        self.signal.readings(self.sample(800))
        self.signal.invalidate()
        self.assertFalse(self.signal.fresh)
        self.assertEqual(self.signal._tick_id, 0)
