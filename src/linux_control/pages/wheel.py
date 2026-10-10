"""Wheel Control embedded in the common native window.

Device writes remain explicit user actions. Discovery and input reads are local;
the page neither changes permissions nor starts privileged helpers.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from wheel_control.devices import DeviceMonitor, discover_wheels
from wheel_control.model import demo_g29
from wheel_control.profiles import ProfileStore
from wheel_control.telemetry import Telemetry
from wheel_control.ui import WheelControlsMixin


CSS = """
.wheel-page .device-hero, .wheel-page .panel, .wheel-page .profile-row { padding: 18px; }
.wheel-page .badge { padding: 6px 10px; border-radius: 8px; font-size: 11px; }
.wheel-page .badge.success { background: #303030; color: #f5f5f5; }
.wheel-page .input-status { border-top: 1px solid #383838; padding-top: 12px; }
.wheel-page .numeric { font-feature-settings: "tnum"; font-weight: 600; }
.wheel-page scale trough { min-height: 4px; }
.wheel-page levelbar trough { background: #333333; border: none; border-radius: 5px; }
.wheel-page levelbar block { min-height: 7px; border-radius: 4px; border: none; }
.wheel-page levelbar block.filled { background: #dedede; }
.wheel-page levelbar block.empty { background: #333333; }
.wheel-page levelbar block.warning { background: #b0b0b0; }
.wheel-page levelbar block.clipping { background: #ffffff; }
.wheel-page button, .wheel-page scale slider, .wheel-page switch {
  transition: background-color 140ms ease-out, border-color 140ms ease-out;
}
.wheel-page.reduce-motion * { transition: none; animation: none; }
"""


class WheelPage(WheelControlsMixin, Gtk.Box):
    def __init__(self, host, translator, settings, *, force_demo=False):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
        self.host = host
        self.tr = translator
        self.settings = settings
        self.add_css_class("wheel-page")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.force_demo = force_demo
        self._demo_device = demo_g29()
        self.devices = []
        self.current_device = None
        self.telemetry_reader = None
        # Preserve profiles from the original application without migrating or
        # overwriting them just because the combined app was opened.
        self.profile_store = ProfileStore()
        self.profiles = self.profile_store.load()
        self._updating_controls = False
        self._refresh_source = 0
        self._ffb_source = 0
        self._demo_source = 0
        self._telemetry_source = 0
        self._closed = False
        self._active = False
        self._loading_devices = False
        self._device_generation = 0
        self._scan_generation = 0
        self._scan_running = False
        self._scan_again = False
        self._selection_generation = 0
        self._device_loading = False
        self._settings_running = False
        self._pending_selection = None
        self._snapshot_device = None
        self._attribute_snapshot = {}
        self._mode_snapshot = []
        self._write_running = False
        self._meter_running = False
        self._pending_telemetry = None
        self._telemetry_lock = threading.Lock()
        self._applied_range = 900
        self._last_telemetry = Telemetry()
        self.reduced_motion = settings.reduced_motion

        self.toast_overlay = Adw.ToastOverlay(vexpand=True)
        self.append(self.toast_overlay)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.toast_overlay.set_child(content)
        content.append(self._page_header())
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_vexpand(True)
        content.append(self.stack)
        self.stack.add_named(self._build_empty_page(), "empty")
        self.stack.add_named(self._build_device_page(), "device")
        self._sync_motion()
        self._bind_static_text(self)
        self.tr.connect(self.retranslate)
        self._install_shortcuts()

        try:
            self.device_monitor = DeviceMonitor(self._hotplug_event)
            self.device_monitor.start()
        except (OSError, RuntimeError):
            self.device_monitor = None
        self._ffb_source = GLib.timeout_add(250, self._poll_ffb_meter)
        self._telemetry_source = GLib.timeout_add(33, self._flush_telemetry)
        self._refresh_source = GLib.idle_add(self.refresh_devices)

    def _page_header(self):
        row = Gtk.Box(spacing=12, margin_top=20, margin_bottom=16,
                      margin_start=24, margin_end=24)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
        title = Gtk.Label(label="Wheel Control", xalign=0)
        title.add_css_class("title-1")
        subtitle = Gtk.Label(label="Live input, wheel settings and game profiles",
                             xalign=0, wrap=True)
        subtitle.add_css_class("dim-label")
        text.append(title)
        text.append(subtitle)
        row.append(text)
        self.device_model = Gtk.StringList()
        self.device_dropdown = Gtk.DropDown(model=self.device_model,
                                           tooltip_text="Active wheel")
        self.device_dropdown.set_visible(False)
        self.device_dropdown.connect("notify::selected", self._on_device_selected)
        row.append(self.device_dropdown)
        self.scan_spinner = Gtk.Spinner()
        row.append(self.scan_spinner)
        self.refresh_button = Gtk.Button(icon_name="view-refresh-symbolic",
                                         tooltip_text="Scan devices (Ctrl+R)")
        self.refresh_button.connect("clicked", lambda _button: self.refresh_devices())
        row.append(self.refresh_button)
        diagnostics = Gtk.Button(icon_name="edit-copy-symbolic",
                                 tooltip_text="Copy Diagnostics  Ctrl+D")
        diagnostics.connect("clicked", self._copy_diagnostics)
        row.append(diagnostics)
        return row

    def _install_shortcuts(self):
        controller = Gtk.ShortcutController()
        controller.set_scope(Gtk.ShortcutScope.MANAGED)
        for key, callback in ((Gdk.KEY_r, self.refresh_devices),
                              (Gdk.KEY_d, lambda: self._copy_diagnostics(None))):
            action = Gtk.CallbackAction.new(
                lambda _widget, _arguments, fn=callback: self._shortcut(fn)
            )
            controller.add_shortcut(Gtk.Shortcut.new(
                Gtk.KeyvalTrigger.new(key, Gdk.ModifierType.CONTROL_MASK), action
            ))
        self.add_controller(controller)

    def _shortcut(self, callback):
        if self._active and not self._closed:
            callback()
            return True
        return False

    def _dialog_parent(self):
        return self.host

    def _tr(self, text):
        dynamic = getattr(self.tr, "dynamic", self.tr)
        return dynamic(text)

    def _bind_static_text(self, widget):
        # Bind source strings once. Language changes never reconstruct controls
        # or reset unsaved slider values and profile selections.
        icon_path = Path(__file__).resolve().parents[1] / "resources" / "wheel.svg"
        if icon_path.exists():
            if isinstance(widget, Gtk.Image) and widget.get_icon_name() == "input-gaming-symbolic":
                widget.set_from_file(str(icon_path))
            elif isinstance(widget, Adw.StatusPage):
                image = Gtk.Image.new_from_file(str(icon_path))
                if image.get_paintable():
                    widget.set_paintable(image.get_paintable())
        pairs = []
        if isinstance(widget, Gtk.Label):
            pairs.append(("get_label", "set_label"))
        elif isinstance(widget, Gtk.Button):
            pairs.append(("get_label", "set_label"))
        elif isinstance(widget, Gtk.Expander):
            pairs.append(("get_label", "set_label"))
        elif isinstance(widget, Adw.PreferencesRow):
            pairs.append(("get_title", "set_title"))
            if isinstance(widget, Adw.ActionRow):
                pairs.append(("get_subtitle", "set_subtitle"))
        elif isinstance(widget, Adw.Banner):
            pairs.append(("get_title", "set_title"))
        elif isinstance(widget, Adw.StatusPage):
            pairs.extend((("get_title", "set_title"),
                          ("get_description", "set_description")))
        pairs.append(("get_tooltip_text", "set_tooltip_text"))
        for getter, setter in pairs:
            source = getattr(widget, getter)()
            if source:
                self.tr.bind(widget, source, setter=setter)
        child = widget.get_first_child()
        while child:
            following = child.get_next_sibling()
            self._bind_static_text(child)
            child = following

    def refresh_devices(self):
        if self._closed:
            return GLib.SOURCE_REMOVE
        self._refresh_source = 0
        if self._scan_running:
            self._scan_again = True
            return GLib.SOURCE_REMOVE
        self._scan_generation += 1
        generation = self._scan_generation
        self._scan_running = True
        self.refresh_button.set_sensitive(False)
        self.scan_spinner.start()

        def discover():
            error = None
            try:
                devices = [self._demo_device] if self.force_demo else discover_wheels()
            except (OSError, RuntimeError, ValueError) as exc:
                devices = []
                error = str(exc)
            GLib.idle_add(self._scan_finished, generation, devices, error)

        threading.Thread(target=discover, name="linux-control-wheel-scan",
                         daemon=True).start()
        return GLib.SOURCE_REMOVE

    def _scan_finished(self, generation, devices, error):
        if self._closed or generation != self._scan_generation:
            return GLib.SOURCE_REMOVE
        self._scan_running = False
        self.scan_spinner.stop()
        self.refresh_button.set_sensitive(True)
        if error:
            self._toast(f"Device scan failed: {error}")
        self._load_devices(devices)
        if self._scan_again:
            self._scan_again = False
            self.refresh_devices()
        return GLib.SOURCE_REMOVE

    def _select_device(self, device):
        # Stop the old reader immediately, then read sysfs on a worker. Old
        # device controls cannot be applied while a new selection is loading.
        self._selection_generation += 1
        generation = self._selection_generation
        super()._select_device(None)
        self._device_loading = device is not None
        self._snapshot_device = None
        if device is None or self._closed:
            self._pending_selection = None
            return
        self.telemetry_columns.set_sensitive(False)
        self.profile_actions.set_sensitive(False)
        self.apply_button.set_sensitive(False)
        self.device_name.set_label(device.name)
        self.device_status.set_label(self._tr("Reading device settings…"))
        self.connection_badge.set_label(self._tr("Loading"))
        if self._settings_running:
            # Coalesce rapid dropdown/hotplug changes rather than starting an
            # unbounded number of driver reads.
            self._pending_selection = (generation, device)
            return
        self._read_device_settings(generation, device)

    def _read_device_settings(self, generation, device):
        self._settings_running = True

        def read_settings():
            defaults = {"range": device.maximum_range, "gain": 65535,
                        "autocenter": 0, "combine_pedals": 0,
                        "spring_level": 100, "damper_level": 100,
                        "friction_level": 100, "ffb_leds": 0}
            values = {}
            for name, default in defaults.items():
                try:
                    values[name] = device.read_attribute(name, default)
                except (OSError, ValueError, RuntimeError):
                    values[name] = default
            try:
                modes = device.alternate_modes()
            except (OSError, ValueError):
                modes = []
            GLib.idle_add(self._settings_ready, generation, device, values, modes)

        threading.Thread(target=read_settings, name="linux-control-wheel-settings",
                         daemon=True).start()

    def _settings_ready(self, generation, device, values, modes):
        self._settings_running = False
        if not self._closed and self._pending_selection:
            next_generation, next_device = self._pending_selection
            self._pending_selection = None
            self._read_device_settings(next_generation, next_device)
            return GLib.SOURCE_REMOVE
        if self._closed or generation != self._selection_generation:
            return GLib.SOURCE_REMOVE
        self._device_loading = False
        self._snapshot_device = device
        self._attribute_snapshot = values
        self._mode_snapshot = modes
        self.telemetry_columns.set_sensitive(True)
        self.profile_actions.set_sensitive(True)
        super()._select_device(device)
        if self._write_running:
            self.apply_button.set_sensitive(False)
        return GLib.SOURCE_REMOVE

    def _attribute_value(self, device, name, default):
        if device is self._snapshot_device:
            return self._attribute_snapshot.get(name, default)
        return default

    def _device_modes(self, device):
        return self._mode_snapshot if device is self._snapshot_device else []

    def _apply_settings(self, _button):
        device = self.current_device
        if device is None or self._write_running or self._closed:
            return
        # GTK values are captured on its main thread; the worker only touches
        # the selected device and ordinary Python data.
        values = {
            "range": self.range_control.get_value(),
            "gain": round(self.gain_control.get_value() * 65535 / 100),
            "autocenter": round(self.autocenter_control.get_value() * 65535 / 100),
            "combine_pedals": int(self.combine_switch.get_active()),
            "spring_level": self.spring_control.get_value(),
            "damper_level": self.damper_control.get_value(),
            "friction_level": self.friction_control.get_value(),
            "ffb_leds": int(self.ffb_leds_switch.get_active()),
        }
        generation = self._device_generation
        self._write_running = True
        self.apply_button.set_sensitive(False)

        def write_settings():
            applied, blocked = [], []
            deadline = time.monotonic() + 8
            items = list(values.items())
            for index, (name, value) in enumerate(items):
                if (self._closed or self.current_device is not device
                        or generation != self._device_generation):
                    break
                if time.monotonic() >= deadline:
                    blocked.extend(item for item, _ in items[index:] if device.supports(item))
                    break
                if not device.supports(name):
                    continue
                if not device.can_write(name):
                    blocked.append(name)
                    continue
                try:
                    device.write_attribute(name, value)
                except (OSError, ValueError, NotImplementedError):
                    blocked.append(name)
                    continue
                applied.append(name)
            GLib.idle_add(self._apply_finished, generation, device, values,
                          applied, blocked)

        threading.Thread(target=write_settings, name="linux-control-wheel-apply",
                         daemon=True).start()

    def _enable_apply(self):
        device = self.current_device
        self.apply_button.set_sensitive(bool(device and any(device.can_write(name)
            for name in ("range", "gain", "autocenter", "combine_pedals",
                         "spring_level", "damper_level", "friction_level", "ffb_leds"))))

    def _apply_finished(self, generation, device, values, applied, blocked):
        self._write_running = False
        if self._closed:
            return GLib.SOURCE_REMOVE
        self._enable_apply()
        if generation != self._device_generation or self.current_device is not device:
            return GLib.SOURCE_REMOVE
        if "range" in applied:
            self._applied_range = values["range"]
            self._update_telemetry(self._last_telemetry)
        if blocked:
            self._toast(f"Applied {len(applied)} settings; unchanged: {', '.join(blocked)}. Check device permissions.")
        else:
            self._toast("Settings applied" if applied else "No writable settings available")
        return GLib.SOURCE_REMOVE

    def _start_demo_animation(self):
        if self._active:
            super()._start_demo_animation()

    def _flush_telemetry(self):
        if self._closed:
            return GLib.SOURCE_REMOVE
        if not self._active:
            return GLib.SOURCE_CONTINUE
        return super()._flush_telemetry()

    def _update_telemetry(self, telemetry):
        self._last_telemetry = telemetry
        return super()._update_telemetry(telemetry)

    def _poll_ffb_meter(self):
        if self._closed:
            return GLib.SOURCE_REMOVE
        if not self._active:
            return GLib.SOURCE_CONTINUE
        device = self.current_device
        if self._meter_running or not device or not device.supports("peak_ffb_level"):
            return GLib.SOURCE_CONTINUE
        generation = self._device_generation
        self._meter_running = True

        def read_meter():
            peak = max(0, device.read_attribute("peak_ffb_level", 0))
            GLib.idle_add(self._meter_ready, generation, device, peak)

        threading.Thread(target=read_meter, name="linux-control-wheel-meter",
                         daemon=True).start()
        return GLib.SOURCE_CONTINUE

    def _meter_ready(self, generation, device, peak):
        self._meter_running = False
        if self._closed or not self._active or generation != self._device_generation or self.current_device is not device:
            return GLib.SOURCE_REMOVE
        ratio = peak / 32768
        self.ffb_meter.set_value(min(1.5, ratio))
        state = "clipping" if ratio > 1 else "near limit" if ratio >= 0.85 else "no clipping"
        self.ffb_meter_label.set_label(self._tr(f"{round(ratio * 100)}% — {state}"))
        return GLib.SOURCE_REMOVE

    def _device_action(self, device, operation, success, failure):
        if self._write_running or self._closed or self.current_device is not device:
            return
        generation = self._device_generation
        self._write_running = True
        self.apply_button.set_sensitive(False)

        def run():
            error = None
            if not self._closed and generation == self._device_generation and self.current_device is device:
                try:
                    operation()
                except (OSError, ValueError, NotImplementedError) as exc:
                    error = str(exc)
            GLib.idle_add(self._device_action_done, generation, device, success,
                          failure, error)

        threading.Thread(target=run, name="linux-control-wheel-action", daemon=True).start()

    def _device_action_done(self, generation, device, success, failure, error):
        self._write_running = False
        if self._closed:
            return GLib.SOURCE_REMOVE
        self._enable_apply()
        if generation == self._device_generation and self.current_device is device:
            self._toast(f"{failure}: {error}" if error else success)
        return GLib.SOURCE_REMOVE

    def _confirm_switch_mode(self, device, mode):
        self._device_action(device, lambda: device.switch_mode(mode),
                            "Switching mode; waiting for the wheel to reconnect",
                            "Could not switch mode")

    def _reset_ffb_peak(self, _button):
        device = self.current_device
        if device and device.supports("peak_ffb_level"):
            self._device_action(device, lambda: device.write_attribute("peak_ffb_level", 0),
                                "Force-feedback peak reset", "Could not reset peak")

    def _toast(self, message):
        if not self._closed:
            self.toast_overlay.add_toast(Adw.Toast(title=self._tr(message), timeout=4))

    def retranslate(self):
        if self._closed:
            return
        self.sync_motion()
        self._update_telemetry(self._last_telemetry)
        if self._device_loading:
            self.device_status.set_label(self._tr("Reading device settings…"))
            self.connection_badge.set_label(self._tr("Loading"))
        device = self.current_device
        if device:
            if device.demo:
                state = "Demo"
            elif self.telemetry_reader and not (self.telemetry_reader._thread and self.telemetry_reader._thread.is_alive()):
                state = "Input unavailable"
            elif self.permission_banner.get_revealed():
                state = "Limited access"
            elif device.attributes or device.ff_capabilities:
                state = "Ready"
            else:
                state = "Input only"
            self.connection_badge.set_label(self._tr(state))
            self._poll_ffb_meter()

    def sync_motion(self):
        desktop = Gtk.Settings.get_default()
        self.reduced_motion = self.settings.reduced_motion or bool(
            desktop and not desktop.get_property("gtk-enable-animations")
        )
        self._sync_motion()

    def set_active(self, active):
        self._active = bool(active) and not self._closed
        self.sync_motion()
        if not self._active and self._demo_source:
            GLib.source_remove(self._demo_source)
            self._demo_source = 0
        if self._active and self.current_device and self.current_device.demo:
            if not self._demo_source:
                self._start_demo_animation()
        if self._active:
            self._flush_telemetry()

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._active = False
        self._scan_generation += 1
        self._selection_generation += 1
        self._pending_selection = None
        if self.telemetry_reader:
            self.telemetry_reader.stop()
            self.telemetry_reader = None
        if self.device_monitor:
            self.device_monitor.stop()
            self.device_monitor = None
        for name in ("_refresh_source", "_ffb_source", "_demo_source",
                     "_telemetry_source"):
            source = getattr(self, name)
            if source:
                GLib.source_remove(source)
                setattr(self, name, 0)
        with self._telemetry_lock:
            self._pending_telemetry = None
