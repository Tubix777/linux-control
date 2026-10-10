"""Read-only decorative circuit and fan activity; no hardware operations."""
from __future__ import annotations

import math
import time
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk


class HardwareSignal(Gtk.DrawingArea):
    """Decorative circuit activity and reported fan activity, never a RPM gauge."""
    def __init__(self, enabled):
        super().__init__()
        self.enabled = enabled
        self.set_content_width(220)
        self.set_content_height(80)
        self.set_hexpand(True)
        self.set_accessible_role(Gtk.AccessibleRole.IMG)
        self.set_draw_func(self._draw)
        self.active = False
        self.fresh = False
        self._read_at = 0.0
        self.has_fan = False
        self.spinning = False
        self.phase = 0.0
        self._tick_id = 0
        self._last_frame = None
        self._origin_frame = None
        self.connect("map", lambda *_: self.sync())
        self.connect("unmap", lambda *_: self.stop())

    def readings(self, sample):
        speeds = [item.get("value") for item in sample.get("sensors") or []
                  if isinstance(item, dict) and item.get("unit") == "RPM"]
        speeds = [v for v in speeds if type(v) in (int, float) and math.isfinite(v) and v >= 0]
        self.has_fan = bool(speeds)
        self.spinning = any(v > 0 for v in speeds)
        self.fresh = True
        self._read_at = time.monotonic()
        self.sync()

    def invalidate(self):
        self.fresh = False
        self.stop()

    def _can_animate(self):
        if self.fresh and time.monotonic() - self._read_at >= 10:
            self.fresh = False
        return self.active and self.fresh and self.enabled() and self.get_mapped()

    def stop(self):
        if self._tick_id:
            self.remove_tick_callback(self._tick_id)
            self._tick_id = 0
        self._last_frame = self._origin_frame = None
        self.queue_draw()

    def sync(self):
        animate = self._can_animate()
        if animate and not self._tick_id:
            self._last_frame = self._origin_frame = None
            self._tick_id = self.add_tick_callback(self._frame)
        elif not animate:
            self.stop()
        self.queue_draw()

    def _frame(self, widget, clock):
        if not self._can_animate():
            self._tick_id = 0
            self._last_frame = self._origin_frame = None
            self.queue_draw()
            return GLib.SOURCE_REMOVE
        now = clock.get_frame_time()
        if self._origin_frame is None:
            self._origin_frame = now
        if self._last_frame is None or now - self._last_frame >= 33_000:
            self._last_frame = now
            self.phase = (now - self._origin_frame) / 1_000_000
            self.queue_draw()
        return GLib.SOURCE_CONTINUE

    def _draw(self, area, cr, width, height):
        cr.save()
        cr.translate(width / 2, height / 2)
        moving = self.active and self.fresh and self.enabled()
        glow = .12 + (.07 * (1 + math.sin(self.phase * 2.5)) if moving else 0)
        cr.set_source_rgba(1, 1, 1, glow)
        cr.arc(-50, 0, 32, 0, math.tau)
        cr.fill()
        cr.set_line_width(1)
        for side in (-1, 1):
            for line in range(3):
                y = (line - 1) * 16
                cr.set_source_rgba(1, 1, 1, .15)
                cr.move_to(-50 + side * 22, y)
                cr.line_to(-50 + side * 47, y)
                cr.line_to(-50 + side * 57, y + side * 10)
                cr.stroke()
                if moving:
                    t = (self.phase * .5 + line * .2) % 1
                    cr.set_source_rgba(1, 1, 1, .65)
                    cr.arc(-50 + side * (23 + t * 23), y, 2, 0, math.tau)
                    cr.fill()
        cr.set_source_rgba(1, 1, 1, .8 if self.fresh else .3)
        cr.rectangle(-68, -18, 36, 36)
        cr.stroke()
        cr.rectangle(-62, -12, 24, 24)
        cr.stroke()
        # The fan rotates only with a positive, fresh sensor readback.
        cr.translate(64, 0)
        cr.set_source_rgba(1, 1, 1, .25)
        cr.arc(0, 0, 29, 0, math.tau)
        cr.stroke()
        cr.set_source_rgba(1, 1, 1, .85 if self.has_fan and self.fresh else .25)
        if moving and self.spinning:
            cr.rotate(self.phase * 2)
        for _ in range(5):
            cr.move_to(3, -2)
            cr.curve_to(8, -17, 22, -20, 22, -8)
            cr.curve_to(18, -1, 9, 5, 3, -2)
            cr.fill()
            cr.rotate(math.tau / 5)
        cr.arc(0, 0, 5, 0, math.tau)
        cr.fill()
        cr.restore()
