from __future__ import annotations

import math
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from . import __version__
from .appearance import THEMES, AppearanceStore, palette_css
from .devices import DeviceMonitor, discover_wheels
from .diagnostics import diagnostics_json
from .linux_input import LinuxInputReader
from .model import WheelDevice, demo_g29
from .profiles import ProfileStore, WheelProfile, export_profile, import_profile
from .telemetry import Telemetry


class WheelGauge(Gtk.DrawingArea):
    def __init__(self) -> None:
        super().__init__()
        self.set_content_width(160)
        self.set_content_height(160)
        self.steering = 0.0
        self.set_draw_func(self._draw)

    def set_steering(self, value: float) -> None:
        value = max(-1.0, min(1.0, value))
        if self.steering == value:
            return
        self.steering = value
        self.queue_draw()

    def _draw(self, _area, context, width: int, height: int) -> None:
        size = min(width, height)
        radius = size * 0.37
        cx, cy = width / 2, height / 2

        context.set_source_rgba(0.045, 0.045, 0.045, 1)
        context.arc(cx, cy, radius * 1.08, 0, math.tau)
        context.fill()

        context.set_source_rgba(0.18, 0.18, 0.18, 1)
        context.arc(cx, cy, radius, 0, math.tau)
        context.set_line_width(size * 0.055)
        context.stroke()

        context.save()
        context.translate(cx, cy)
        context.set_source_rgba(0.48, 0.48, 0.48, 0.8)
        context.set_line_width(size * 0.008)
        for index in range(11):
            angle = math.radians(-135 + index * 27)
            inner = radius * (0.79 if index in {0, 5, 10} else 0.84)
            outer = radius * 0.94
            context.move_to(math.sin(angle) * inner, -math.cos(angle) * inner)
            context.line_to(math.sin(angle) * outer, -math.cos(angle) * outer)
        context.stroke()
        context.restore()

        context.save()
        context.translate(cx, cy)
        context.rotate(self.steering * math.radians(135))
        context.set_source_rgba(0.82, 0.82, 0.82, 1)
        context.set_line_width(size * 0.035)
        context.set_line_cap(1)
        context.move_to(0, -radius * 0.86)
        context.line_to(0, radius * 0.23)
        context.stroke()
        context.restore()

        context.set_source_rgba(0.82, 0.82, 0.82, 1)
        context.arc(cx, cy, size * 0.052, 0, math.tau)
        context.fill()
        context.set_source_rgba(0.98, 0.98, 0.98, 0.9)
        context.arc(cx, cy, size * 0.018, 0, math.tau)
        context.fill()


class ControlScale(Gtk.Box):
    def __init__(
        self, title: str, subtitle: str, minimum: int, maximum: int, suffix: str
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.minimum = minimum
        self.maximum = maximum
        heading = Gtk.Box(spacing=12)
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        title_label = Gtk.Label(label=title, xalign=0)
        title_label.add_css_class("heading")
        subtitle_label = Gtk.Label(label=subtitle, xalign=0, wrap=True)
        subtitle_label.add_css_class("dim-label")
        subtitle_label.add_css_class("caption")
        self.value_label = Gtk.Label(xalign=1)
        self.value_label.add_css_class("numeric")
        heading.append(text_box)
        text_box.append(title_label)
        text_box.append(subtitle_label)
        heading.append(self.value_label)
        self.scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, minimum, maximum, 1
        )
        self.scale.set_draw_value(False)
        self.scale.set_hexpand(True)
        self.scale.set_tooltip_text(title)
        self.scale.connect("value-changed", self._update_label, suffix)
        self.append(heading)
        self.append(self.scale)
        self._update_label(self.scale, suffix)

    def _update_label(self, scale: Gtk.Scale, suffix: str) -> None:
        self.value_label.set_label(f"{int(scale.get_value())}{suffix}")

    def set_value(self, value: int) -> None:
        self.scale.set_value(max(self.minimum, min(self.maximum, value)))

    def get_value(self) -> int:
        return int(self.scale.get_value())


class WheelControlsMixin:
    """Reusable controls and device lifecycle for a window or an embedded page."""

    def _dialog_parent(self):
        return self

    def _tr(self, text):
        return text

    def _alert_dialog(self, **kwargs):
        return Adw.AlertDialog(**{key: self._tr(value) for key, value in kwargs.items()})

    def _file_dialog(self, **kwargs):
        if "title" in kwargs:
            kwargs["title"] = self._tr(kwargs["title"])
        return Gtk.FileDialog(**kwargs)

    def _attribute_value(self, device, name, default):
        return device.read_attribute(name, default)

    def _device_modes(self, device):
        return device.alternate_modes()

    def _build_header(self) -> None:
        header = Adw.HeaderBar()
        header.add_css_class("top-bar")
        title = Adw.WindowTitle(title="Wheel Control")
        header.set_title_widget(title)
        self.device_model = Gtk.StringList()
        self.device_dropdown = Gtk.DropDown(model=self.device_model)
        self.device_dropdown.set_tooltip_text("Active wheel")
        self.device_dropdown.connect("notify::selected", self._on_device_selected)
        header.pack_start(self.device_dropdown)
        refresh = Gtk.Button(
            icon_name="view-refresh-symbolic",
            tooltip_text="Scan devices (Ctrl+R)",
        )
        refresh.connect("clicked", lambda _button: self.refresh_devices())
        header.pack_end(refresh)
        menu = Gtk.MenuButton(icon_name="open-menu-symbolic")
        popover = Gtk.Popover()
        menu_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            margin_top=8,
            margin_bottom=8,
            margin_start=8,
            margin_end=8,
        )
        appearance_label = Gtk.Label(
            label="Appearance / Görünüm", xalign=0, margin_bottom=6
        )
        appearance_label.add_css_class("heading")
        menu_box.append(appearance_label)
        self.theme_ids = list(THEMES)
        self.theme_dropdown = Gtk.DropDown(
            model=Gtk.StringList.new(list(THEMES.values()))
        )
        self.theme_dropdown.set_tooltip_text("Application theme")
        self.theme_dropdown.set_selected(self.theme_ids.index(self.theme))
        self.theme_dropdown.connect("notify::selected", self._change_theme)
        menu_box.append(self.theme_dropdown)
        self.motion_toggle = Gtk.CheckButton(
            label="Reduce motion", margin_top=10, active=self.reduced_motion
        )
        self.motion_toggle.set_tooltip_text(
            "Disable decorative transitions; live input remains immediate"
        )
        self.motion_toggle.connect("toggled", self._change_motion)
        menu_box.append(self.motion_toggle)
        menu_box.append(Gtk.Separator(margin_top=10, margin_bottom=6))
        about = Gtk.Button(label="About Wheel Control")
        about.add_css_class("flat")
        about.connect("clicked", self._show_about)
        diagnostics = Gtk.Button(label="Copy Diagnostics  Ctrl+D")
        diagnostics.add_css_class("flat")
        diagnostics.connect("clicked", self._copy_diagnostics)
        menu_box.append(diagnostics)
        menu_box.append(about)
        popover.set_child(menu_box)
        menu.set_popover(popover)
        header.pack_end(menu)
        self.toolbar_view.add_top_bar(header)

    def _change_theme(self, dropdown, _param) -> None:
        selected = dropdown.get_selected()
        if selected >= len(self.theme_ids):
            return
        theme = self.theme_ids[selected]
        if theme == self.theme:
            return
        try:
            self.appearance_store.save(theme)
        except (OSError, ValueError) as exc:
            dropdown.set_selected(self.theme_ids.index(self.theme))
            self._toast(f"Could not save appearance: {exc}")
            return
        self.theme = theme
        load_css(theme)

    def _sync_motion(self) -> None:
        if self.reduced_motion:
            self.add_css_class("reduce-motion")
        else:
            self.remove_css_class("reduce-motion")
        self.stack.set_transition_duration(0 if self.reduced_motion else 160)

    def _change_motion(self, toggle) -> None:
        enabled = toggle.get_active()
        if enabled == self.reduced_motion:
            return
        try:
            self.appearance_store.save_reduced_motion(enabled)
        except (OSError, ValueError) as exc:
            toggle.set_active(self.reduced_motion)
            self._toast(f"Could not save motion preference: {exc}")
            return
        self.reduced_motion = enabled
        self._sync_motion()

    def _install_actions(self, application: Adw.Application) -> None:
        actions = {
            "refresh": lambda: self.refresh_devices(),
            "copy-diagnostics": lambda: self._copy_diagnostics(None),
            "close": self.close,
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _action, _parameter, fn=callback: fn())
            self.add_action(action)
        application.set_accels_for_action("win.refresh", ["<Control>r", "F5"])
        application.set_accels_for_action("win.copy-diagnostics", ["<Control>d"])
        application.set_accels_for_action("win.close", ["<Control>q"])

    def _build_empty_page(self) -> Gtk.Widget:
        page = Adw.StatusPage()
        page.set_icon_name("input-gaming-symbolic")
        page.set_title("No racing wheel detected")
        page.set_description(
            "Connect your Logitech wheel by USB, switch it to PC/PS3 mode when applicable, then scan again."
        )
        actions = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER)
        scan = Gtk.Button(label="Scan Again")
        scan.add_css_class("suggested-action")
        scan.add_css_class("pill")
        scan.connect("clicked", lambda _button: self.refresh_devices())
        demo = Gtk.Button(label="Open Demo")
        demo.add_css_class("pill")
        demo.connect("clicked", lambda _button: self._load_devices([self._demo_device]))
        actions.append(scan)
        actions.append(demo)
        page.set_child(actions)
        return page

    def _build_device_page(self) -> Gtk.Widget:
        clamp = Adw.Clamp(maximum_size=1180, tightening_threshold=1050)
        scrolled = Gtk.ScrolledWindow(vexpand=True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        clamp.set_child(scrolled)
        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20,
            margin_top=8,
            margin_bottom=28,
            margin_start=28,
            margin_end=28,
        )
        scrolled.set_child(content)

        hero = Gtk.Box(spacing=18)
        hero.add_css_class("card")
        hero.add_css_class("device-hero")
        icon = Gtk.Image.new_from_icon_name("input-gaming-symbolic")
        icon.set_pixel_size(28)
        hero.append(icon)
        hero_text = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER
        )
        self.device_name = Gtk.Label(xalign=0)
        self.device_name.add_css_class("title-2")
        self.device_status = Gtk.Label(xalign=0)
        self.device_status.add_css_class("dim-label")
        hero_text.append(self.device_name)
        hero_text.append(self.device_status)
        hero.append(hero_text)
        self.connection_badge = Gtk.Label(
            label="Connected",
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER,
            hexpand=True,
        )
        self.connection_badge.add_css_class("success")
        self.connection_badge.add_css_class("badge")
        hero.append(self.connection_badge)
        content.append(hero)

        self.mode_banner = Adw.Banner(
            title="G29 is in PS4 mode. Move the hardware selector to PS3, then reconnect it to enable Linux force feedback and range control."
        )
        self.mode_banner.set_revealed(False)
        content.append(self.mode_banner)
        self.permission_banner = Adw.Banner(
            title="Some settings are read-only. The packaged udev rule requires administrator installation; then reconnect the wheel."
        )
        content.append(self.permission_banner)

        columns = Gtk.Box(spacing=18, homogeneous=True)
        self.telemetry_columns = columns
        columns.set_orientation(Gtk.Orientation.HORIZONTAL)
        columns.set_spacing(20)
        self.control_columns = columns
        content.append(columns)

        telemetry_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        telemetry_card.add_css_class("card")
        telemetry_card.add_css_class("panel")
        telemetry_title = Gtk.Label(label="Live input", xalign=0)
        telemetry_title.add_css_class("title-3")
        telemetry_card.append(telemetry_title)
        self.gauge = WheelGauge()
        self.gauge.set_halign(Gtk.Align.CENTER)
        telemetry_card.append(self.gauge)
        self.angle_label = Gtk.Label(label="0°", xalign=0.5)
        self.angle_label.add_css_class("title-2")
        telemetry_card.append(self.angle_label)
        pedals = Gtk.Grid(column_spacing=12, row_spacing=12)
        self.pedal_bars = {}
        self.pedal_values = {}
        for row, (key, label) in enumerate(
            (("throttle", "Throttle"), ("brake", "Brake"), ("clutch", "Clutch"))
        ):
            bar = Gtk.LevelBar(min_value=0, max_value=1)
            bar.set_value(0)
            bar.set_hexpand(True)
            bar.set_valign(Gtk.Align.CENTER)
            bar.set_tooltip_text(label)
            text = Gtk.Label(label=label, xalign=0)
            text.add_css_class("caption")
            value = Gtk.Label(label="0%", width_chars=4, xalign=1)
            value.add_css_class("numeric")
            pedals.attach(text, 0, row, 1, 1)
            pedals.attach(bar, 1, row, 1, 1)
            pedals.attach(value, 2, row, 1, 1)
            self.pedal_bars[key] = bar
            self.pedal_values[key] = value
        telemetry_card.append(pedals)
        input_status = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        input_status.add_css_class("input-status")
        self.dpad_label = Gtk.Label(label="D-pad: centered", xalign=0)
        self.button_label = Gtk.Label(label="Buttons: none", xalign=0, ellipsize=3)
        self.dpad_label.add_css_class("caption")
        self.button_label.add_css_class("caption")
        input_status.append(self.dpad_label)
        input_status.append(self.button_label)
        telemetry_card.append(input_status)
        columns.append(telemetry_card)

        settings = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        settings.add_css_class("card")
        settings.add_css_class("panel")
        settings_title = Gtk.Label(label="Wheel settings", xalign=0)
        settings_title.add_css_class("title-3")
        settings.append(settings_title)

        self.mode_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        mode_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        mode_title = Gtk.Label(label="Compatibility mode", xalign=0)
        mode_title.add_css_class("heading")
        mode_subtitle = Gtk.Label(
            label="Re-enumerates the wheel for older games", xalign=0
        )
        mode_subtitle.add_css_class("dim-label")
        mode_subtitle.add_css_class("caption")
        mode_text.append(mode_title)
        mode_text.append(mode_subtitle)
        self.mode_model = Gtk.StringList()
        self.mode_dropdown = Gtk.DropDown(model=self.mode_model)
        self.mode_dropdown.set_hexpand(True)
        mode_actions = Gtk.Box(spacing=10)
        switch_mode = Gtk.Button(label="Switch")
        switch_mode.connect("clicked", self._switch_mode)
        self.mode_row.append(mode_text)
        mode_actions.append(self.mode_dropdown)
        mode_actions.append(switch_mode)
        self.mode_row.append(mode_actions)
        self.mode_row.set_visible(False)
        settings.append(self.mode_row)
        self.range_control = ControlScale(
            "Rotation range", "Maximum steering lock", 40, 900, "°"
        )
        self.gain_control = ControlScale(
            "Force feedback", "Global effect strength", 0, 100, "%"
        )
        self.autocenter_control = ControlScale(
            "Auto-center", "Centers the wheel outside games", 0, 100, "%"
        )
        for control in (self.range_control, self.gain_control, self.autocenter_control):
            settings.append(control)
        self.combine_switch = Adw.SwitchRow(
            title="Combine pedals",
            subtitle="Expose throttle and brake as a single axis",
        )
        pedal_preferences = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        pedal_preferences.add_css_class("boxed-list")
        pedal_preferences.append(self.combine_switch)
        settings.append(pedal_preferences)

        self.advanced_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.spring_control = ControlScale(
            "Spring", "Strength of spring effects", 0, 100, "%"
        )
        self.damper_control = ControlScale(
            "Damper", "Strength of damper effects", 0, 100, "%"
        )
        self.friction_control = ControlScale(
            "Friction", "Strength of friction effects", 0, 100, "%"
        )
        for control in (
            self.spring_control,
            self.damper_control,
            self.friction_control,
        ):
            self.advanced_box.append(control)
        self.ffb_leds_switch = Adw.SwitchRow(
            title="Clipping LEDs",
            subtitle="Use the wheel LEDs as a live force-feedback meter",
        )
        led_preferences = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        led_preferences.add_css_class("boxed-list")
        led_preferences.append(self.ffb_leds_switch)
        self.advanced_box.append(led_preferences)
        self.advanced_expander = Gtk.Expander(label="Advanced force effects")
        self.advanced_expander.set_child(self.advanced_box)
        settings.append(self.advanced_expander)
        self.apply_button = Gtk.Button(label="Apply")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.add_css_class("pill")
        self.apply_button.set_halign(Gtk.Align.END)
        self.apply_button.connect("clicked", self._apply_settings)
        settings.append(self.apply_button)
        columns.append(settings)

        self.ffb_meter_card = Gtk.Box(spacing=14)
        self.ffb_meter_card.add_css_class("card")
        self.ffb_meter_card.add_css_class("profile-row")
        meter_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        meter_title = Gtk.Label(label="Force-feedback peak", xalign=0)
        meter_title.add_css_class("heading")
        self.ffb_meter_label = Gtk.Label(label="0% — no clipping", xalign=0)
        self.ffb_meter_label.add_css_class("dim-label")
        meter_text.append(meter_title)
        meter_text.append(self.ffb_meter_label)
        self.ffb_meter = Gtk.LevelBar(min_value=0, max_value=1.5, hexpand=True)
        self.ffb_meter.add_offset_value("warning", 0.85)
        self.ffb_meter.add_offset_value("clipping", 1.0)
        reset_peak = Gtk.Button(label="Reset Peak")
        reset_peak.connect("clicked", self._reset_ffb_peak)
        self.ffb_meter_card.append(meter_text)
        self.ffb_meter_card.append(self.ffb_meter)
        self.ffb_meter_card.append(reset_peak)
        content.append(self.ffb_meter_card)

        profile_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        profile_card.add_css_class("card")
        profile_card.add_css_class("profile-row")
        profile_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        profile_title = Gtk.Label(label="Profiles", xalign=0)
        profile_title.add_css_class("heading")
        profile_subtitle = Gtk.Label(label="Save these settings for a game", xalign=0)
        profile_subtitle.add_css_class("dim-label")
        profile_text.append(profile_title)
        profile_text.append(profile_subtitle)
        profile_card.append(profile_text)
        profile_actions = Gtk.Box(spacing=8)
        self.profile_actions = profile_actions
        profile_card.append(profile_actions)
        self.profile_model = Gtk.StringList.new(
            [profile.name for profile in self.profiles]
        )
        self.profile_dropdown = Gtk.DropDown(model=self.profile_model)
        self.profile_dropdown.set_hexpand(True)
        profile_actions.append(self.profile_dropdown)
        load_profile = Gtk.Button(label="Load")
        load_profile.connect("clicked", self._load_profile)
        save_profile = Gtk.Button(label="Save Current")
        save_profile.connect("clicked", self._save_profile)
        new_profile = Gtk.Button(
            icon_name="list-add-symbolic", tooltip_text="Create profile"
        )
        new_profile.connect("clicked", self._new_profile)
        import_profile_button = Gtk.Button(
            icon_name="document-open-symbolic", tooltip_text="Import profile"
        )
        import_profile_button.connect("clicked", self._import_profile)
        export_profile_button = Gtk.Button(
            icon_name="document-save-symbolic", tooltip_text="Export profile"
        )
        export_profile_button.connect("clicked", self._export_profile)
        delete_profile = Gtk.Button(
            icon_name="user-trash-symbolic", tooltip_text="Delete profile"
        )
        delete_profile.connect("clicked", self._delete_profile)
        profile_actions.append(load_profile)
        profile_actions.append(save_profile)
        profile_actions.append(new_profile)
        profile_actions.append(import_profile_button)
        profile_actions.append(export_profile_button)
        profile_actions.append(delete_profile)
        content.append(profile_card)
        return clamp

    def refresh_devices(self) -> bool:
        if self._closed:
            return GLib.SOURCE_REMOVE
        if self._refresh_source:
            GLib.source_remove(self._refresh_source)
        self._refresh_source = 0
        try:
            devices = [self._demo_device] if self.force_demo else discover_wheels()
        except (OSError, RuntimeError, ValueError) as exc:
            self._toast(f"Device scan failed: {exc}")
            devices = []
        self._load_devices(devices)
        return GLib.SOURCE_REMOVE

    def _load_devices(self, devices: list[WheelDevice]) -> None:
        previous_identifier = (
            self.current_device.identifier if self.current_device else None
        )
        self.devices = devices
        self._loading_devices = True
        while self.device_model.get_n_items():
            self.device_model.remove(0)
        for device in devices:
            self.device_model.append(device.name)
        self.device_dropdown.set_visible(bool(devices))
        if not devices:
            self._loading_devices = False
            self._select_device(None)
            self.stack.set_visible_child_name("empty")
            return
        selected_index = next(
            (
                index
                for index, device in enumerate(devices)
                if device.identifier == previous_identifier
            ),
            0,
        )
        self.device_dropdown.set_selected(selected_index)
        self._loading_devices = False
        self._select_device(devices[selected_index])
        self.stack.set_visible_child_name("device")

    def _on_device_selected(self, dropdown: Gtk.DropDown, _param) -> None:
        if self._loading_devices or self._closed:
            return
        index = dropdown.get_selected()
        if 0 <= index < len(self.devices):
            self._select_device(self.devices[index])

    def _select_device(self, device: WheelDevice | None) -> None:
        self._device_generation += 1
        self._pending_telemetry = None
        if self._demo_source:
            GLib.source_remove(self._demo_source)
            self._demo_source = 0
        if self.telemetry_reader:
            self.telemetry_reader.stop()
            self.telemetry_reader = None
        self.current_device = device
        self._update_telemetry(Telemetry())
        if device is None:
            return
        self.device_name.set_label(device.name)
        node = str(device.event_node) if device.event_node else self._tr("simulated input")
        firmware = (
            f"  •  fw {device.firmware_revision}" if device.firmware_revision else ""
        )
        self.device_status.set_label(
            f"{device.vendor_id}:{device.product_id}  •  {device.driver}{firmware}  •  {node}"
        )
        self.connection_badge.remove_css_class("success")
        self.connection_badge.remove_css_class("warning")
        if device.demo:
            self.connection_badge.set_label(self._tr("Demo"))
        elif device.attributes or device.ff_capabilities:
            self.connection_badge.set_label(self._tr("Ready"))
            self.connection_badge.add_css_class("success")
        else:
            self.connection_badge.set_label(self._tr("Input only"))
            self.connection_badge.add_css_class("warning")
        self.mode_banner.set_revealed(device.product_id == "c260")
        modes = self._device_modes(device)
        self._mode_ids = [mode_id for mode_id, _label, _selected in modes]
        while self.mode_model.get_n_items():
            self.mode_model.remove(0)
        selected_mode = 0
        for index, (_mode_id, label, selected) in enumerate(modes):
            self.mode_model.append(label)
            if selected:
                selected_mode = index
        self.mode_dropdown.set_selected(selected_mode)
        self.mode_row.set_visible(bool(modes))
        self.mode_row.set_sensitive(device.can_write("alternate_modes"))
        self.range_control.minimum = device.minimum_range
        self.range_control.maximum = device.maximum_range
        self.range_control.scale.set_range(device.minimum_range, device.maximum_range)
        self._updating_controls = True
        self.range_control.set_value(
            self._attribute_value(device, "range", device.maximum_range)
        )
        self._applied_range = self.range_control.get_value()
        self.gain_control.set_value(
            round(self._attribute_value(device, "gain", 65535) * 100 / 65535)
        )
        self.autocenter_control.set_value(
            round(self._attribute_value(device, "autocenter", 0) * 100 / 65535)
        )
        self.combine_switch.set_active(bool(self._attribute_value(device, "combine_pedals", 0)))
        self.spring_control.set_value(self._attribute_value(device, "spring_level", 100))
        self.damper_control.set_value(self._attribute_value(device, "damper_level", 100))
        self.friction_control.set_value(self._attribute_value(device, "friction_level", 100))
        self.ffb_leds_switch.set_active(bool(self._attribute_value(device, "ffb_leds", 0)))
        self._updating_controls = False

        self.range_control.set_sensitive(device.can_write("range"))
        self.gain_control.set_sensitive(device.can_write("gain"))
        self.autocenter_control.set_sensitive(device.can_write("autocenter"))
        self.combine_switch.set_sensitive(device.can_write("combine_pedals"))
        advanced = {
            "spring_level": self.spring_control,
            "damper_level": self.damper_control,
            "friction_level": self.friction_control,
        }
        for name, control in advanced.items():
            control.set_sensitive(device.can_write(name))
        self.ffb_leds_switch.set_sensitive(device.can_write("ffb_leds"))
        locked = [
            name
            for name in (
                "range",
                "gain",
                "autocenter",
                "combine_pedals",
                *advanced,
                "ffb_leds",
                "alternate_modes",
            )
            if device.supports(name) and not device.can_write(name)
        ]
        self.permission_banner.set_revealed(bool(locked))
        if locked:
            self.connection_badge.set_label(self._tr("Limited access"))
            self.connection_badge.remove_css_class("success")
            self.connection_badge.add_css_class("warning")
        for name, control in {
            "range": self.range_control,
            "gain": self.gain_control,
            "autocenter": self.autocenter_control,
            "combine_pedals": self.combine_switch,
            **advanced,
            "ffb_leds": self.ffb_leds_switch,
        }.items():
            control.set_tooltip_text(
                self._tr("Read-only: device permission required") if name in locked else None
            )
        self.advanced_expander.set_visible(
            any(device.supports(name) for name in advanced)
            or device.supports("ffb_leds")
        )
        self.ffb_meter_card.set_visible(device.supports("peak_ffb_level"))
        self.apply_button.set_sensitive(
            any(
                device.can_write(name)
                for name in (
                    "range",
                    "gain",
                    "autocenter",
                    "combine_pedals",
                    *advanced,
                    "ffb_leds",
                )
            )
        )

        if device.demo:
            self._start_demo_animation()
        elif device.event_node:
            generation = self._device_generation
            self.telemetry_reader = LinuxInputReader(
                device.event_node,
                lambda telemetry: self._telemetry_from_thread(telemetry, generation),
                axis_codes=device.axis_codes,
            )
            if not self.telemetry_reader.start():
                self.connection_badge.set_label(self._tr("Input unavailable"))
                self.connection_badge.remove_css_class("success")
                self.connection_badge.add_css_class("warning")
                self._toast(
                    "Live input is unavailable. Check device permissions and reconnect the wheel."
                )

    def _start_demo_animation(self) -> None:
        self._demo_tick = 0

        def tick() -> bool:
            if not self.current_device or not self.current_device.demo:
                return GLib.SOURCE_REMOVE
            self._demo_tick += 1
            phase = self._demo_tick / 35
            self._update_telemetry(
                Telemetry(
                    steering=math.sin(phase) * 0.72,
                    throttle=(math.sin(phase * 0.71) + 1) / 2,
                    brake=(math.sin(phase * 0.47 + 2.1) + 1) / 4,
                    clutch=(math.sin(phase * 0.35 + 4.2) + 1) / 5,
                )
            )
            return GLib.SOURCE_CONTINUE

        self._demo_source = GLib.timeout_add(40, tick)

    def _telemetry_from_thread(self, telemetry: Telemetry, generation: int) -> None:
        with self._telemetry_lock:
            if self._closed:
                return
            self._pending_telemetry = (generation, telemetry)

    def _flush_telemetry(self) -> bool:
        if self._closed:
            return GLib.SOURCE_REMOVE
        with self._telemetry_lock:
            pending = self._pending_telemetry
            self._pending_telemetry = None
        if pending and pending[0] == self._device_generation and not self._closed:
            self._update_telemetry(pending[1])
        return GLib.SOURCE_CONTINUE

    def _update_telemetry(self, telemetry: Telemetry) -> bool:
        self.gauge.set_steering(telemetry.steering)
        steering_range = self._applied_range
        self._set_live_label(
            self.angle_label, f"{round(telemetry.steering * steering_range / 2):+d}°"
        )
        for key, label in self.pedal_values.items():
            value = getattr(telemetry, key)
            bar = self.pedal_bars[key]
            if bar.get_value() != value:
                bar.set_value(value)
            self._set_live_label(label, f"{value:.0%}")
        directions = {
            (0, 0): "centered",
            (0, -1): "up",
            (1, -1): "up-right",
            (1, 0): "right",
            (1, 1): "down-right",
            (0, 1): "down",
            (-1, 1): "down-left",
            (-1, 0): "left",
            (-1, -1): "up-left",
        }
        self._set_live_label(
            self.dpad_label,
            self._tr(f"D-pad: {directions.get((telemetry.hat_x, telemetry.hat_y), 'unknown')}"),
        )
        buttons = ", ".join(str(code) for code in telemetry.pressed_buttons)
        self._set_live_label(self.button_label, self._tr(f"Buttons: {buttons or 'none'}"))
        return GLib.SOURCE_REMOVE

    @staticmethod
    def _set_live_label(label: Gtk.Label, text: str) -> None:
        if label.get_label() != text:
            label.set_label(text)

    def _apply_settings(self, _button) -> None:
        device = self.current_device
        if device is None:
            return
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
        applied = []
        blocked = []
        for name, value in values.items():
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
            if name == "range":
                self._applied_range = value
        if blocked:
            self._toast(
                f"Applied {len(applied)} settings; unchanged: {', '.join(blocked)}. Check device permissions."
            )
        else:
            self._toast(
                "Settings applied" if applied else "No writable settings available"
            )

    def _profile_from_controls(self, name: str) -> WheelProfile:
        return WheelProfile(
            name=name,
            rotation_range=self.range_control.get_value(),
            gain=self.gain_control.get_value(),
            autocenter=self.autocenter_control.get_value(),
            combine_pedals=self.combine_switch.get_active(),
            spring_level=self.spring_control.get_value(),
            damper_level=self.damper_control.get_value(),
            friction_level=self.friction_control.get_value(),
            ffb_leds=self.ffb_leds_switch.get_active(),
        )

    def _load_profile(self, _button) -> None:
        index = self.profile_dropdown.get_selected()
        if index >= len(self.profiles):
            return
        profile = self.profiles[index]
        self.range_control.set_value(profile.rotation_range)
        self.gain_control.set_value(profile.gain)
        self.autocenter_control.set_value(profile.autocenter)
        self.combine_switch.set_active(profile.combine_pedals)
        self.spring_control.set_value(profile.spring_level)
        self.damper_control.set_value(profile.damper_level)
        self.friction_control.set_value(profile.friction_level)
        self.ffb_leds_switch.set_active(profile.ffb_leds)
        self._toast(f"Loaded {profile.name} — press Apply to send to wheel")

    def _save_profile(self, _button) -> None:
        index = self.profile_dropdown.get_selected()
        if index >= len(self.profiles):
            return
        name = self.profiles[index].name
        updated = list(self.profiles)
        updated[index] = self._profile_from_controls(name)
        try:
            self.profile_store.save(updated)
        except (OSError, ValueError) as exc:
            self._toast(f"Could not save profile: {exc}")
            return
        self.profiles = updated
        self._toast(f"Saved {name}")

    def _new_profile(self, _button) -> None:
        dialog = self._alert_dialog(
            heading="Create Profile",
            body="Choose a short name such as Rally, Drift, or F1.",
        )
        entry = Gtk.Entry(placeholder_text=self._tr("Profile name"), activates_default=True)
        entry.set_max_length(40)
        dialog.set_extra_child(entry)
        dialog.add_response("cancel", self._tr("Cancel"))
        dialog.add_response("create", self._tr("Create"))
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("create")
        dialog.set_close_response("cancel")

        def response(_dialog, response_id: str) -> None:
            if response_id != "create" or self._closed:
                return
            self._create_profile(entry.get_text())

        dialog.connect("response", response)
        dialog.present(self._dialog_parent())

    def _create_profile(self, name: str) -> None:
        name = name.strip()
        if not name:
            self._toast("Profile name cannot be empty")
            return
        if any(profile.name.casefold() == name.casefold() for profile in self.profiles):
            self._toast("A profile with that name already exists")
            return
        updated = [*self.profiles, self._profile_from_controls(name)]
        try:
            self.profile_store.save(updated)
        except (OSError, ValueError) as exc:
            self._toast(f"Could not create profile: {exc}")
            return
        # Publish the new selection only after its durable save succeeds.
        self.profiles = updated
        self.profile_model.append(name)
        self.profile_dropdown.set_selected(len(updated) - 1)
        self._toast(f"Created {name}")

    def _delete_profile(self, _button) -> None:
        index = self.profile_dropdown.get_selected()
        if index >= len(self.profiles):
            return
        if len(self.profiles) == 1:
            self._toast("At least one profile is required")
            return
        name = self.profiles[index].name
        dialog = self._alert_dialog(
            heading="Delete profile?",
            body=f"“{name}” will be removed. Settings on the wheel will not change.",
        )
        dialog.add_response("cancel", self._tr("Cancel"))
        dialog.add_response("delete", self._tr("Delete"))
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        target = self.profiles[index]

        def response(_dialog, response_id: str) -> None:
            if response_id == "delete" and not self._closed and target in self.profiles:
                self._confirm_delete_profile(self.profiles.index(target))

        dialog.connect("response", response)
        dialog.present(self._dialog_parent())

    def _confirm_delete_profile(self, index: int) -> None:
        if len(self.profiles) <= 1:
            return
        name = self.profiles[index].name
        updated = self.profiles[:index] + self.profiles[index + 1 :]
        try:
            self.profile_store.save(updated)
        except (OSError, ValueError) as exc:
            self._toast(f"Could not delete profile: {exc}")
            return
        self.profiles = updated
        self.profile_model.remove(index)
        self.profile_dropdown.set_selected(min(index, len(updated) - 1))
        self._toast(f"Deleted {name}")

    def _export_profile(self, _button) -> None:
        index = self.profile_dropdown.get_selected()
        if index >= len(self.profiles):
            return
        profile = self.profiles[index]
        filename = (
            profile.name.replace("/", "_").replace("\\", "_").strip(".") or "profile"
        )
        dialog = self._file_dialog(
            title="Export Profile",
            initial_name=f"{filename}.wheel-profile.json",
        )

        def done(file_dialog: Gtk.FileDialog, result) -> None:
            if self._closed:
                return
            try:
                selected = file_dialog.save_finish(result)
                path = selected.get_path()
                if path is None:
                    raise ValueError("Only local files are supported")
                export_profile(profile, Path(path))
            except GLib.Error as exc:
                if not exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self._toast(f"Could not export profile: {exc.message}")
                return
            except (OSError, ValueError) as exc:
                self._toast(f"Could not export profile: {exc}")
                return
            self._toast(f"Exported {profile.name}")

        dialog.save(self._dialog_parent(), None, done)

    def _import_profile(self, _button) -> None:
        dialog = self._file_dialog(title="Import Profile")

        def done(file_dialog: Gtk.FileDialog, result) -> None:
            if self._closed:
                return
            try:
                selected = file_dialog.open_finish(result)
                path = selected.get_path()
                if path is None:
                    raise ValueError("Only local files are supported")
                profile = import_profile(Path(path))
                if any(
                    item.name.casefold() == profile.name.casefold()
                    for item in self.profiles
                ):
                    raise ValueError(f"A profile named {profile.name} already exists")
                updated = [*self.profiles, profile]
                self.profile_store.save(updated)
            except GLib.Error as exc:
                if not exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self._toast(f"Could not import profile: {exc.message}")
                return
            except (OSError, ValueError) as exc:
                self._toast(f"Could not import profile: {exc}")
                return
            self.profiles = updated
            self.profile_model.append(profile.name)
            self.profile_dropdown.set_selected(len(updated) - 1)
            self._toast(f"Imported {profile.name}")

        dialog.open(self._dialog_parent(), None, done)

    def _copy_diagnostics(self, _button) -> None:
        self.get_clipboard().set(diagnostics_json(self.devices))
        self._toast("Diagnostics copied to clipboard")

    def _switch_mode(self, _button) -> None:
        device = self.current_device
        selected = self.mode_dropdown.get_selected()
        if device is None or selected >= len(getattr(self, "_mode_ids", [])):
            return
        mode = self._mode_ids[selected]
        dialog = self._alert_dialog(
            heading="Switch compatibility mode?",
            body="The wheel will disconnect and reconnect. Close your game first and keep your hands clear: the wheel may calibrate.",
        )
        dialog.add_response("cancel", self._tr("Cancel"))
        dialog.add_response("switch", self._tr("Switch Mode"))
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        def response(_dialog, response_id: str) -> None:
            if response_id == "switch" and self.current_device is device:
                self._confirm_switch_mode(device, mode)

        dialog.connect("response", response)
        dialog.present(self._dialog_parent())

    def _confirm_switch_mode(self, device: WheelDevice, mode: str) -> None:
        try:
            device.switch_mode(mode)
        except (OSError, ValueError) as exc:
            self._toast(f"Could not switch mode: {exc}")
            return
        self._toast("Switching mode; waiting for the wheel to reconnect")

    def _poll_ffb_meter(self) -> bool:
        device = self.current_device
        if device is None or not device.supports("peak_ffb_level"):
            return GLib.SOURCE_CONTINUE
        peak = max(0, device.read_attribute("peak_ffb_level", 0))
        ratio = peak / 32768
        self.ffb_meter.set_value(min(1.5, ratio))
        percent = round(ratio * 100)
        state = (
            "clipping"
            if ratio > 1
            else "near limit"
            if ratio >= 0.85
            else "no clipping"
        )
        self.ffb_meter_label.set_label(self._tr(f"{percent}% — {state}"))
        return GLib.SOURCE_CONTINUE

    def _reset_ffb_peak(self, _button) -> None:
        device = self.current_device
        if device is None or not device.supports("peak_ffb_level"):
            return
        try:
            device.write_attribute("peak_ffb_level", 0)
        except (OSError, NotImplementedError) as exc:
            self._toast(f"Could not reset peak: {exc}")
            return
        self._toast("Force-feedback peak reset")

    def _hotplug_event(self) -> None:
        GLib.idle_add(self._queue_hotplug_refresh)

    def _queue_hotplug_refresh(self) -> bool:
        if self._closed:
            return GLib.SOURCE_REMOVE
        if self._refresh_source:
            GLib.source_remove(self._refresh_source)
        self._refresh_source = GLib.timeout_add(450, self.refresh_devices)
        return GLib.SOURCE_REMOVE

    def _show_about(self, _button) -> None:
        about = Adw.AboutDialog(
            application_name="Wheel Control",
            application_icon="io.github.tubix777.WheelControl",
            version=__version__,
            developer_name="Wheel Control contributors",
            comments="A native Linux control center for racing wheels.",
            license_type=Gtk.License.GPL_3_0,
        )
        about.present(self._dialog_parent())

    def _toast(self, message: str) -> None:
        self.toast_overlay.add_toast(Adw.Toast(title=message, timeout=4))

    def _on_close(self, _window) -> bool:
        if self._closed:
            return False
        self._closed = True
        if self.telemetry_reader:
            self.telemetry_reader.stop()
            self.telemetry_reader = None
        if self.device_monitor:
            self.device_monitor.stop()
            self.device_monitor = None
        for name in (
            "_refresh_source",
            "_ffb_source",
            "_demo_source",
            "_telemetry_source",
        ):
            source = getattr(self, name)
            if source:
                GLib.source_remove(source)
                setattr(self, name, 0)
        with self._telemetry_lock:
            self._pending_telemetry = None
        application = self.get_application()
        if application is not None and application.window is self:
            application.window = None
        return False


class WheelWindow(WheelControlsMixin, Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application, force_demo: bool = False) -> None:
        super().__init__(application=application)
        self.add_css_class("wheel-window")
        self.set_title("Wheel Control")
        self.set_default_size(980, 850)
        self.set_size_request(760, 560)
        self.force_demo = force_demo
        self._demo_device = demo_g29()
        self.devices: list[WheelDevice] = []
        self.current_device: WheelDevice | None = None
        self.telemetry_reader: LinuxInputReader | None = None
        self.profile_store = ProfileStore()
        self.profiles = self.profile_store.load()
        self._updating_controls = False
        self._refresh_source = 0
        self._ffb_source = 0
        self._demo_source = 0
        self._closed = False
        self._loading_devices = False
        self._device_generation = 0
        self._pending_telemetry = None
        self._telemetry_lock = threading.Lock()
        self._applied_range = 900
        self.appearance_store = AppearanceStore()
        self.theme = self.appearance_store.load()
        self.reduced_motion = self.appearance_store.load_reduced_motion()

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        self.toolbar_view = Adw.ToolbarView()
        self.toast_overlay.set_child(self.toolbar_view)
        self._build_header()
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self._sync_motion()
        self.stack.set_vexpand(True)
        self.toolbar_view.set_content(self.stack)
        self.stack.add_named(self._build_empty_page(), "empty")
        self.stack.add_named(self._build_device_page(), "device")
        self._install_actions(application)

        self.connect("close-request", self._on_close)
        try:
            self.device_monitor: DeviceMonitor | None = DeviceMonitor(
                self._hotplug_event
            )
            self.device_monitor.start()
        except OSError:
            self.device_monitor = None
        self._ffb_source = GLib.timeout_add(250, self._poll_ffb_meter)
        self._telemetry_source = GLib.timeout_add(33, self._flush_telemetry)
        self._refresh_source = GLib.idle_add(self.refresh_devices)



_css_provider = None


def load_css(theme: str | None = None) -> None:
    global _css_provider
    theme = theme or AppearanceStore().load()
    Adw.StyleManager.get_default().set_color_scheme(
        Adw.ColorScheme.FORCE_LIGHT if theme == "light" else Adw.ColorScheme.FORCE_DARK
    )
    css_path = Path(__file__).parent / "resources" / "style.css"
    provider = Gtk.CssProvider()
    provider.load_from_string(
        palette_css(theme) + "\n" + css_path.read_text(encoding="utf-8")
    )
    display = Gtk.Widget.get_display(Gtk.Label())
    if display:
        if _css_provider is not None:
            Gtk.StyleContext.remove_provider_for_display(display, _css_provider)
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        _css_provider = provider
