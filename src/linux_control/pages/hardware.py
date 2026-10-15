"""Anvil's hardware adapters in the common GTK window.

Discovery and polling are read-only. Every mutation starts with an explicit
button action; motherboard fan writes stay in Anvil's packaged helper.
"""
from collections import deque
import csv
from datetime import datetime
import io
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import threading
import time

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from anvil.backend import Monitor, profile_names, set_profile
from anvil.fans import FAN_PRESETS, channels, fan_result, preset_points
from anvil.insights import SensorStats, ThermalAlerts
from anvil.fan_history import FanRpmHistory
from anvil.rgb import parse_devices
from linux_control.motion import HardwareSignal
from linux_control.design import heading
from linux_control.entrance import MotionBox

HELPER = Path("/usr/libexec/anvil-fan-helper")


def safe_helper(path=HELPER):
    """Do not execute a writable, symlinked or user-owned privileged program."""
    try:
        if path.is_symlink():
            return False
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            return False
        if not info.st_mode & 0o111:
            return False
        for parent in path.parents:
            item = parent.stat()
            if item.st_uid != 0 or item.st_mode & 0o022:
                return False
        return True
    except OSError:
        return False


def fan_command(channel, action, points=None, *, helper=HELPER, monitor_only=False):
    """Revalidate the current physical channel immediately before pkexec."""
    if monitor_only:
        raise ValueError("Bu kurulumda donanım değiştirme kapalı.")
    if type(channel) is not int or action not in ("curve", "full", "restore"):
        raise ValueError("Geçersiz fan işlemi.")
    if not safe_helper(helper) or not shutil.which("pkexec"):
        raise ValueError("Paketli fan yardımcısı bulunamadı; fan kontrolü kapalı.")
    if channel not in [item["channel"] for item in channels()]:
        raise ValueError("Güvenli fan kanalı artık kullanılamıyor.")
    args = ["/usr/bin/pkexec", str(helper), str(channel), action]
    if action == "curve":
        if (not isinstance(points, list) or len(points) != 5
                or any(not isinstance(p, list) or len(p) != 2
                       or any(type(v) is not int for v in p) for p in points)):
            raise ValueError("Fan eğrisi beş tam sayı noktasından oluşmalı.")
        # These limits match the helper, which independently validates again.
        temperatures = [p[0] for p in points]
        duties = [p[1] for p in points]
        if (not all(20 <= value <= 85 for value in temperatures)
                or temperatures != sorted(set(temperatures))
                or not all(50 <= value <= 100 for value in duties)
                or duties != sorted(duties) or duties[-2:] != [100, 100]):
            raise ValueError("Fan eğrisi güvenli sıcaklık ve hız sınırlarına uymuyor.")
        args.append(json.dumps(points, separators=(",", ":")))
    return args


def execute(args, timeout=30):
    try:
        process = subprocess.run(args, capture_output=True, text=True,
                                 timeout=timeout, env={**os.environ, "LC_ALL": "C"})
        return process.returncode == 0, process.stdout[-20000:], process.stderr[-2000:]
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as error:
        return False, "", str(error)


def csv_text(samples):
    output = io.StringIO(newline="")
    fields = ("time", "cpu_usage", "cpu_temp", "gpu_usage", "gpu_temp",
              "memory_used", "memory_total", "disk_used", "disk_total")
    writer = csv.DictWriter(output, fields)
    writer.writeheader()
    for sample in samples:
        gpu = sample.get("gpu") or {}
        writer.writerow({**{key: sample.get(key) for key in fields if not key.startswith("gpu_")},
                         "gpu_usage": gpu.get("usage"), "gpu_temp": gpu.get("temperature")})
    return output.getvalue()


def diagnostic_text(identity, sample, fan_channels):
    # No DMI serial identifiers, personal application logs, or PCI output.
    keys = ("board", "vendor", "bios", "bios_date", "os", "kernel", "cpu")
    readings = [{key: row.get(key) for key in ("chip", "label", "unit", "value")}
                for row in sample.get("sensors", [])]
    return json.dumps({"application": "Uzeyir Control", "module": "Anvil Control",
                       "created": datetime.now().isoformat(timespec="seconds"),
                       "identity": {key: identity.get(key) for key in keys},
                       "cpu_usage": sample.get("cpu_usage"),
                       "cpu_temp": sample.get("cpu_temp"), "gpu": sample.get("gpu"),
                       "sensors": readings, "safe_fan_channels": fan_channels},
                      ensure_ascii=False, indent=2) + "\n"


def percent(used, total):
    if type(used) not in (int, float) or type(total) not in (int, float) or total <= 0:
        return None
    if not math.isfinite(used) or not math.isfinite(total):
        return None
    return max(0.0, min(100.0, 100.0 * used / total))


class HistoryChart(Gtk.DrawingArea):
    """Bounded source-backed history; gaps remain gaps rather than fake zeros."""
    def __init__(self, translator):
        super().__init__()
        self.tr = translator
        self.set_content_height(148)
        self.set_hexpand(True)
        self.samples = deque(maxlen=120)
        self.set_draw_func(self._draw)
        self.set_accessible_role(Gtk.AccessibleRole.IMG)

    def add(self, sample):
        self.samples.append(sample)
        self.queue_draw()

    def _draw(self, area, cr, width, height):
        cr.select_font_face("Manrope")
        left, top, bottom = 34, 10, height - 23
        right = width - 12
        cr.set_line_width(1)
        for value in (0, 25, 50, 75, 100):
            y = bottom - (bottom - top) * value / 100
            cr.set_source_rgba(1, 1, 1, .08)
            cr.move_to(left, y)
            cr.line_to(right, y)
            cr.stroke()
            cr.set_source_rgb(.56, .56, .56)
            cr.set_font_size(10)
            cr.move_to(2, y + 3)
            cr.show_text(str(value))
        rows = list(self.samples)
        colors = ((.97, .97, .97), (.55, .55, .55))
        for key, color in zip(("cpu_usage", "gpu_usage"), colors):
            cr.set_source_rgb(*color)
            cr.set_line_width(2)
            pen_down = False
            for i, sample in enumerate(rows):
                value = sample.get("cpu_usage") if key == "cpu_usage" else (sample.get("gpu") or {}).get("usage")
                if type(value) not in (int, float) or not math.isfinite(value):
                    cr.stroke()
                    pen_down = False
                    continue
                x = left + (right - left) * i / max(1, len(rows) - 1)
                y = bottom - (bottom - top) * max(0, min(100, value)) / 100
                (cr.line_to if pen_down else cr.move_to)(x, y)
                pen_down = True
            cr.stroke()
        cr.set_source_rgb(.68, .68, .68)
        cr.set_font_size(11)
        cr.move_to(left, height - 5)
        cr.show_text(self.tr("Son 120 ölçüm · CPU / GPU kullanımı (%)"))


class HardwarePage(Gtk.Box):
    def __init__(self, host, translator, settings):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("hardware-page")
        self.host, self.tr, self.settings = host, translator, settings
        self._closed = False
        self._active = False
        self._paused = False
        self._busy = False
        self._polling = False
        self._generation = 0
        self._source = 0
        self._motion = 0
        self._monitor = None
        self._identity = {}
        self._sample = {}
        self._last_success = 0
        self._last_fan_success = 0
        self._fan_channels = []
        self._profile_ids = []
        self._rgb_devices = []
        self._rgb_modes = []
        self._history = deque(maxlen=3600)
        self._stats = SensorStats()
        self._alerts = ThermalAlerts()
        self._fan_history = FanRpmHistory()
        self._sensor_rows = {}
        self._display_values = {}
        self._targets = {}
        self._messages = {}
        self._control_widgets = []
        self._fan_widgets = []
        self._monitor_only = os.environ.get("ANVIL_MONITOR_ONLY") == "1"
        self._build()
        self.tr.connect(self.retranslate)

    def label(self, source, css=None):
        label = Gtk.Label(xalign=0, wrap=True)
        self.tr.bind(label, source)
        if css:
            label.add_css_class(css)
        return label

    def button(self, source, callback, css="soft"):
        button = Gtk.Button()
        self.tr.bind(button, source)
        button.add_css_class(css)
        button.connect("clicked", callback)
        return button

    def _message(self, widget, source, **values):
        """Keep message sources so live statuses also follow a language change."""
        self._messages[widget] = (source, values)
        translated = {key: self.tr(value) if isinstance(value, str) else value for key, value in values.items()}
        message = self.tr(source, **translated)
        widget.set_label(self.tr.dynamic(message) if hasattr(self.tr, "dynamic") else message)

    def card(self, heading):
        box = MotionBox(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("card")
        box.append(self.label(heading, "title-3"))
        return box

    def _build(self):
        scroll = Gtk.ScrolledWindow(hexpand=True, vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp = Adw.Clamp(hexpand=True, unit=Adw.LengthUnit.PX, maximum_size=1180, tightening_threshold=1050)
        clamp.set_child(scroll)
        self.append(clamp)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20,
                               margin_top=30, margin_bottom=32, margin_start=28, margin_end=28)
        scroll.set_child(self.content)
        self.signal = HardwareSignal(self._animations_enabled)
        self.signal.set_hexpand(False)
        self.signal.set_tooltip_text(self.tr("Devre hareketi görseldir; fan yalnız pozitif, güncel RPM okumasında döner. Hızı ölçekli değildir."))
        self.content.append(heading(self.tr, "ANVIL CONTROL", "Sistemin, canlı.",
                                   "Kullanımı, sıcaklıkları ve fanları tek bakışta takip et.", self.signal))
        self.identity_label = self.label("Donanım bilgileri okunuyor…", "machine-identity")
        self.content.append(self.identity_label)
        toolbar = Gtk.Box(spacing=8)
        toolbar.add_css_class("hardware-toolbar")
        self.pause_button = self.button("Duraklat", self._toggle_pause)
        toolbar.append(self.pause_button)
        toolbar.append(self.button("CSV kaydet", lambda *_: self._export("csv")))
        toolbar.append(self.button("JSON raporu", lambda *_: self._export("json")))
        self.live_label = self.label("İlk ölçüm bekleniyor", "live-state")
        self.live_label.set_wrap(False)
        self.live_label.set_hexpand(True)
        self.live_label.set_halign(Gtk.Align.END)
        toolbar.append(self.live_label)
        self.content.append(toolbar)

        self.metrics = {}
        grid = Gtk.FlowBox(column_spacing=14, row_spacing=14, homogeneous=True,
                           min_children_per_line=2, max_children_per_line=4,
                           selection_mode=Gtk.SelectionMode.NONE)
        self.metric_grid = grid
        for i, (key, name) in enumerate((("cpu", "İşlemci"), ("gpu", "Ekran kartı"),
                                         ("memory", "Bellek"), ("disk", "Sistem diski"))):
            card = self.card(name)
            card.add_css_class("metric-card")
            value = Gtk.Label(label="—", xalign=0)
            value.add_css_class("metric")
            bar = Gtk.ProgressBar()
            bar.add_css_class("metric-bar")
            detail = Gtk.Label(label=self.tr("Veri bekleniyor"), xalign=0, wrap=True)
            detail.set_max_width_chars(22)
            detail.add_css_class("muted")
            card.append(value)
            card.append(bar)
            card.append(detail)
            grid.append(card)
            self.metrics[key] = (value, bar, detail)
        self.content.append(grid)
        history = self.card("Canlı performans")
        self.chart = HistoryChart(self.tr)
        history.append(self.chart)
        self.content.append(history)

        sensors = self.card("Sensörler ve fan devirleri")
        self.search = Gtk.SearchEntry(hexpand=True)
        self.tr.bind(self.search, "Sensör ara…", "set_placeholder_text")
        self.search.connect("search-changed", self._filter_sensors)
        sensors.append(self.search)
        sensors.append(self.label("Güncel değer · Oturumdaki en düşük / en yüksek", "muted"))
        self.sensor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sensors.append(self.sensor_box)
        self.sensor_empty = self.label("Sürücü tarafından sunulan sensör bulunamadı.", "muted")
        sensors.append(self.sensor_empty)
        self.content.append(sensors)

        controls = Gtk.Expander()
        self.tr.bind(controls, "Donanım kontrolleri")
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, margin_top=14)
        controls.set_child(section)
        section.append(self.label("Ayarlar yalnızca Uygula düğmesine bastığında değişir.", "muted"))
        power = self.card("Güç profili")
        row = Gtk.Box(spacing=8)
        self.profile_selector = Gtk.DropDown(model=Gtk.StringList.new([]), hexpand=True)
        row.append(self.profile_selector)
        self.profile_apply = self.button("Uygula", self._apply_profile, "primary")
        self._control_widgets.append(self.profile_apply)
        row.append(self.profile_apply)
        power.append(row)
        self.power_status = self.label("Sistemin sunduğu güç profilleri bekleniyor.", "muted")
        power.append(self.power_status)
        section.append(power)

        fan = self.card("Anakart fan kontrolü")
        self.fan_selector = Gtk.DropDown(model=Gtk.StringList.new([]), hexpand=True)
        self.fan_selector.connect("notify::selected", lambda *_: self._fan_detail())
        fan.append(self.fan_selector)
        row = Gtk.Box(spacing=8)
        self.preset_selector = Gtk.DropDown(model=Gtk.StringList.new([self.tr(v[0]) for v in FAN_PRESETS.values()]), hexpand=True)
        row.append(self.preset_selector)
        preset = self.button("Eğriyi uygula", self._apply_preset, "primary")
        row.append(preset)
        fan.append(row)
        row = Gtk.Box(spacing=8)
        full = self.button("Tam hız", lambda *_: self._fan_action("full"))
        restore = self.button("Önceki ayarı geri al", lambda *_: self._fan_action("restore"))
        row.append(full)
        row.append(restore)
        fan.append(row)
        self._fan_widgets.extend((self.fan_selector, self.preset_selector, preset, full, restore))
        self.fan_details = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.fan_details.add_css_class("muted")
        fan.append(self.fan_details)
        self.fan_status = self.label("Paketli fan yardımcısı ve doğrulanmış kanal gerekiyor.", "muted")
        fan.append(self.fan_status)
        self.custom_points = []
        custom = Gtk.Expander()
        self.tr.bind(custom, "Özel fan eğrisi")
        point_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12)
        for temperature, duty in preset_points("balanced"):
            row = Gtk.Box(spacing=8)
            row.append(Gtk.Label(label="°C", xalign=0))
            temp = Gtk.SpinButton.new_with_range(20, 85, 1)
            temp.set_value(temperature)
            row.append(temp)
            row.append(Gtk.Label(label="%", xalign=0))
            speed = Gtk.SpinButton.new_with_range(50, 100, 1)
            speed.set_value(duty)
            row.append(speed)
            self.custom_points.append((temp, speed))
            self._fan_widgets.extend((temp, speed))
            point_box.append(row)
        custom_apply = self.button("Özel eğriyi uygula", self._apply_custom, "primary")
        self._fan_widgets.append(custom_apply)
        point_box.append(custom_apply)
        point_box.append(self.label("20–85 °C arasında artan sıcaklıklar; azalmayan hız ve son iki noktada %100 gerekiyor.", "muted"))
        custom.set_child(point_box)
        fan.append(custom)
        section.append(fan)

        rgb = self.card("RGB · OpenRGB")
        row = Gtk.Box(spacing=8)
        self.rgb_selector = Gtk.DropDown(model=Gtk.StringList.new([]), hexpand=True)
        self.rgb_selector.connect("notify::selected", self._rgb_selection)
        row.append(self.rgb_selector)
        self.rgb_scan = self.button("Cihazları tara", self._scan_rgb)
        row.append(self.rgb_scan)
        rgb.append(row)
        self.rgb_mode = Gtk.DropDown(model=Gtk.StringList.new([]), hexpand=True)
        rgb.append(self.rgb_mode)
        row = Gtk.Box(spacing=8)
        self.rgb_color = Gtk.ColorDialogButton(dialog=Gtk.ColorDialog(with_alpha=False), hexpand=True)
        color = Gdk.RGBA()
        color.parse("#ffffff")
        self.rgb_color.set_rgba(color)
        self.tr.bind(self.rgb_color, "Renk seç", "set_tooltip_text")
        row.append(self.rgb_color)
        self.rgb_apply = self.button("Rengi / modu uygula", self._apply_rgb, "primary")
        self._control_widgets.append(self.rgb_apply)
        row.append(self.rgb_apply)
        rgb.append(row)
        self.rgb_status = self.label("OpenRGB aygıtları henüz taranmadı.", "muted")
        rgb.append(self.rgb_status)
        section.append(rgb)
        self.content.append(controls)

        alerts = Gtk.Box(spacing=12)
        alerts.append(self.label("Sıcaklık uyarısı", "muted"))
        self.alert_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.alert_switch.connect("notify::active", lambda *_: self._alerts.active.clear())
        alerts.append(self.alert_switch)
        self.threshold = Gtk.SpinButton.new_with_range(50, 105, 1)
        self.threshold.set_value(85)
        alerts.append(self.threshold)
        alerts.append(Gtk.Label(label="°C"))
        self.content.append(alerts)
        self.content.append(self.label("Uyarı eşiği bir bildirim tercihidir; donanımın güvenli sıcaklık sınırı değildir.", "muted"))
        self.status = Gtk.Label(xalign=0, wrap=True, selectable=True)
        self.status.add_css_class("muted")
        self.content.append(self.status)
        self._sync_controls()

    def set_active(self, active):
        if self._closed:
            return
        self._active = bool(active)
        self.signal.active = bool(active) and not self._paused
        self.signal.sync()
        if active and not self._source:
            self._source = GLib.timeout_add(2000, self._tick)
        if active and not self._paused:
            self._request_sample()
        if not active and self._source:
            GLib.source_remove(self._source)
            self._source = 0
        if not active:
            self._cancel_motion()
        self._sync_controls()

    def _tick(self):
        if self._closed or not self._active:
            self._source = 0
            return GLib.SOURCE_REMOVE
        if not self._paused and not self._busy:
            self._request_sample()
        return GLib.SOURCE_CONTINUE

    def _request_sample(self):
        if self._polling or self._closed:
            return
        self._polling = True
        generation = self._generation
        def worker():
            try:
                if self._monitor is None:
                    self._monitor = Monitor()
                sample = self._monitor.sample()
                identity = self._monitor.identity
                try:
                    fan_channels = channels(board=identity.get("board"), vendor=identity.get("vendor"))
                    fan_error = False
                except Exception:
                    fan_channels, fan_error = [], True
                GLib.idle_add(self._received, identity, sample, fan_channels, fan_error, generation)
            except Exception:
                GLib.idle_add(self._sample_failed)
        threading.Thread(target=worker, name="hardware-telemetry", daemon=True).start()

    def _sample_failed(self):
        self._polling = False
        self.signal.invalidate()
        if not self._closed:
            self._message(self.live_label, "Ölçüm okunamadı; yeniden denenecek.")
            self._last_fan_success = 0
            self._sync_controls()
        return GLib.SOURCE_REMOVE

    def _received(self, identity, sample, fan_channels, fan_error, generation=None):
        self._polling = False
        if self._closed or self._paused or not self._active:
            return GLib.SOURCE_REMOVE
        if generation is not None and (generation != self._generation or self._busy):
            if not self._busy:
                self._request_sample()
            return GLib.SOURCE_REMOVE
        self._identity, self._sample = identity, sample
        self.signal.readings(sample)
        self._last_success = time.monotonic()
        self._last_fan_success = 0 if fan_error else self._last_success
        self._fan_channels = fan_channels
        self._history.append(sample)
        self._stats.add(sample.get("sensors") or [])
        self._fan_history.record(sample["time"], fan_channels)
        self.chart.add(sample)
        self.identity_label.set_label(f'{identity.get("cpu", "—")}\n{identity.get("board", "—")} · {identity.get("os", "Linux")}')
        self._message(self.live_label, "Canlı · 2 saniyede bir")
        gpu = sample.get("gpu") or {}
        self._targets = {"cpu": sample.get("cpu_usage"), "gpu": gpu.get("usage"),
                         "memory": percent(sample.get("memory_used"), sample.get("memory_total")),
                         "disk": percent(sample.get("disk_used"), sample.get("disk_total"))}
        self._render_details()
        self._animate_metrics()
        self._render_sensors()
        self._refresh_control_data()
        if self.alert_switch.get_active():
            events = self._alerts.check({"CPU": sample.get("cpu_temp"), "GPU": gpu.get("temperature")}, self.threshold.get_value())
            if events:
                self._message(self.status, "\n".join(events))
                application = self.host.get_application()
                if application:
                    notification = Gio.Notification.new(self.tr("Sıcaklık uyarısı"))
                    notification.set_body("\n".join(events))
                    application.send_notification("hardware-temperature", notification)
        return GLib.SOURCE_REMOVE

    def _render_details(self):
        sample, gpu = self._sample, self._sample.get("gpu") or {}
        cpu_temp = sample.get("cpu_temp")
        mhz = sample.get("cpu_mhz")
        cpu_detail = f'{cpu_temp:.0f} °C' if cpu_temp is not None else self.tr("Sıcaklık verisi yok")
        if mhz is not None:
            cpu_detail += f" · {mhz / 1000:.2f} GHz"
        self.metrics["cpu"][2].set_label(cpu_detail)
        gpu_detail = gpu.get("name") or self.tr("GPU telemetrisi kullanılamıyor")
        if gpu.get("temperature") is not None:
            gpu_detail += f' · {gpu["temperature"]:.0f} °C'
        if gpu.get("power") is not None:
            gpu_detail += f' · {gpu["power"]:.0f} W'
        if gpu.get("fan") is not None:
            gpu_detail += f' · {gpu["fan"]:.0f}% {self.tr("fan")}'
        if gpu.get("fan_rpm") is not None:
            gpu_detail += f' · {gpu["fan_rpm"]:.0f} RPM'
        self.metrics["gpu"][2].set_label(gpu_detail)
        for key, prefix in (("memory", "memory"), ("disk", "disk")):
            used, total = sample.get(prefix + "_used"), sample.get(prefix + "_total")
            detail = f"{used / 2**30:.1f} / {total / 2**30:.1f} GiB" if used is not None and total else self.tr("Veri yok")
            self.metrics[key][2].set_label(detail)

    def _cancel_motion(self):
        if self._motion:
            self.remove_tick_callback(self._motion)
            self._motion = 0

    def _animate_metrics(self):
        self._cancel_motion()
        initial = dict(self._display_values)
        if not self._animations_enabled() or not self._active:
            self._set_metric_values(self._targets)
            return
        started = time.monotonic()
        def tick(widget, clock):
            t = min(1, (time.monotonic() - started) / .38)
            eased = 1 - (1 - t) ** 3
            values = {}
            for key, target in self._targets.items():
                if target is None:
                    values[key] = None
                else:
                    start = initial.get(key)
                    if start is None:
                        start = target
                    values[key] = start + (target - start) * eased
            self._set_metric_values(values)
            if t >= 1 or self._closed or not self._active or not self._animations_enabled():
                self._set_metric_values(self._targets)
                self._motion = 0
                return GLib.SOURCE_REMOVE
            return GLib.SOURCE_CONTINUE
        self._motion = self.add_tick_callback(tick)

    def _set_metric_values(self, values):
        self._display_values = dict(values)
        for key, value in values.items():
            label, bar, _ = self.metrics[key]
            label.set_label("—" if value is None else f"{value:.0f}%")
            bar.set_fraction(0 if value is None else max(0, min(1, value / 100)))

    def _render_sensors(self):
        readings = self._sample.get("sensors") or []
        present = set()
        for sensor in readings:
            key = sensor["path"]
            present.add(key)
            if key not in self._sensor_rows:
                box = Gtk.Box(spacing=16)
                title = Gtk.Label(xalign=0, hexpand=True, wrap=True)
                value = Gtk.Label(xalign=1, selectable=True)
                box.append(title)
                box.append(value)
                self.sensor_box.append(box)
                self._sensor_rows[key] = (box, title, value)
            box, title, value = self._sensor_rows[key]
            title.set_label(f'{sensor["chip"]} · {sensor["label"]}')
            low, high = self._stats.values[key]
            format_number = (lambda number: f"{number:.0f}") if sensor["unit"] == "RPM" else (lambda number: f"{number:.1f}")
            value.set_label(f'{format_number(sensor["value"])} {sensor["unit"]}  ·  {format_number(low)} / {format_number(high)}')
        for key in tuple(self._sensor_rows):
            if key not in present:
                self.sensor_box.remove(self._sensor_rows.pop(key)[0])
        self.sensor_empty.set_visible(not readings)
        self._filter_sensors()

    def _filter_sensors(self, *_):
        query = self.search.get_text().casefold().strip()
        for box, title, _ in self._sensor_rows.values():
            box.set_visible(query in title.get_label().casefold())

    def _refresh_control_data(self):
        available = profile_names(self._sample.get("profiles"))
        if available != self._profile_ids:
            self._profile_ids = available
            self.profile_selector.set_model(Gtk.StringList.new([self.tr(p) for p in available]))
            active = self._sample.get("profile")
            if active in available:
                self.profile_selector.set_selected(available.index(active))
        active = self._sample.get("profile")
        if active:
            self._message(self.power_status, "Etkin profil: {profile}", profile=active)
        else:
            self._message(self.power_status, "Güç profili servisi veri sunmuyor.")
        old = self._selected_channel()
        self.fan_selector.set_model(Gtk.StringList.new([self.tr("Kanal {channel}", channel=item["channel"]) for item in self._fan_channels]))
        if old in [row["channel"] for row in self._fan_channels]:
            self.fan_selector.set_selected([row["channel"] for row in self._fan_channels].index(old))
        if not safe_helper() or not self._fan_channels:
            self._message(self.fan_status, "Paketli fan yardımcısı ve doğrulanmış kanal gerekiyor.")
        self._fan_detail()
        self._sync_controls()

    def _selected_channel(self):
        index = self.fan_selector.get_selected()
        return self._fan_channels[index]["channel"] if index < len(self._fan_channels) else None

    def _fan_detail(self):
        channel = self._selected_channel()
        item = next((row for row in self._fan_channels if row["channel"] == channel), None)
        if item is None:
            self.fan_details.set_label(self.tr("Bu anakartta güvenli fan yazımı kullanılamıyor."))
            return
        points = " · ".join(f"{temp:.0f} °C → {speed:.0f}%" for temp, speed in item["points"])
        detail = f'{item.get("rpm", "—")} RPM · {item.get("source_label", "—")} {item.get("source_temp", "—")} °C\n{points}'
        summary = self._fan_history.summary(channel)
        detail += "\n" + (self.tr.dynamic(summary) if hasattr(self.tr, "dynamic") else summary)
        for key, label, unit in (("step_up_ms", "Yükselme", "ms"), ("step_down_ms", "Düşme", "ms"), ("temp_tolerance_c", "Tolerans", "°C")):
            if item.get(key) is not None:
                detail += f' · {self.tr(label)} {item[key]:.0f} {unit}'
        diagnostic = self._fan_history.diagnostic_summary(channel)
        if diagnostic:
            detail += "\n" + (self.tr.dynamic(diagnostic) if hasattr(self.tr, "dynamic") else diagnostic)
        self.fan_details.set_label(detail)

    def _sync_controls(self):
        available = not self._closed and not self._busy and not self._paused and self._active and not self._monitor_only
        self.profile_apply.set_sensitive(available and bool(self._profile_ids))
        self.rgb_apply.set_sensitive(available and bool(self._rgb_devices) and bool(self._rgb_modes))
        self.rgb_scan.set_sensitive(not self._busy and bool(shutil.which("openrgb")))
        fan_ready = available and bool(self._fan_channels) and safe_helper() and 0 < time.monotonic() - self._last_fan_success < 10
        for control in self._fan_widgets:
            control.set_sensitive(fan_ready)

    def _toggle_pause(self, *_):
        self._paused = not self._paused
        self.signal.active = not self._paused and self._active
        self.signal.invalidate()
        self.pause_button.set_label(self.tr("Sürdür" if self._paused else "Duraklat"))
        if self._paused:
            self._last_fan_success = 0
            self._fan_history.clear()
            self._cancel_motion()
            self._message(self.live_label, "Duraklatıldı · Son ölçüm")
        else:
            self._request_sample()
        self._sync_controls()

    def _operation(self, worker, finished):
        if self._busy or self._closed:
            return
        self._busy = True
        self._generation += 1
        self._last_fan_success = 0
        self._sync_controls()
        def run():
            try:
                result = worker()
            except Exception as error:
                result = (False, "", str(error))
            def done():
                self._busy = False
                if not self._closed:
                    finished(result)
                    self._sync_controls()
                    if self._active and not self._paused:
                        self._request_sample()
                return GLib.SOURCE_REMOVE
            GLib.idle_add(done)
        threading.Thread(target=run, name="hardware-action", daemon=True).start()

    def _apply_profile(self, *_):
        if not self.profile_apply.get_sensitive():
            return
        index = self.profile_selector.get_selected()
        if index >= len(self._profile_ids):
            return
        profile = self._profile_ids[index]
        self._message(self.power_status, "Güç profili uygulanıyor…")
        def finished(result):
            ok, message = result if len(result) == 2 else (False, result[-1])
            self._message(self.power_status, message)
            self._message(self.status, message)
        self._operation(lambda: set_profile(profile), finished)

    def _apply_preset(self, *_):
        index = self.preset_selector.get_selected()
        keys = list(FAN_PRESETS)
        if index < len(keys):
            self._fan_action("curve", preset_points(keys[index]))

    def _apply_custom(self, *_):
        self._fan_action("curve", [[temp.get_value_as_int(), speed.get_value_as_int()] for temp, speed in self.custom_points])

    def _fan_action(self, action, points=None):
        if (self._busy or self._paused or self._closed or not self._active
                or self._monitor_only or not 0 < time.monotonic() - self._last_fan_success < 10):
            self._message(self.fan_status, "Yeni başarılı fan ölçümü bekleniyor.")
            return
        channel = self._selected_channel()
        self._last_fan_success = 0
        self._message(self.fan_status, "Fan ayarı uygulanıyor ve geri okunuyor…")
        def worker():
            return execute(fan_command(channel, action, points, monitor_only=self._monitor_only))
        def finished(result):
            ok, output, error = result
            verified, message = fan_result(ok, output, error, action, channel, points)
            self._message(self.fan_status, message)
            self._message(self.status, message)
        self._operation(worker, finished)

    def _scan_rgb(self, *_):
        path = shutil.which("openrgb")
        if not path or self._busy:
            return
        self._message(self.rgb_status, "RGB aygıtları taranıyor…")
        def finished(result):
            ok, output, error = result
            self._rgb_devices = parse_devices(output) if ok else []
            self.rgb_selector.set_model(Gtk.StringList.new([item["name"] for item in self._rgb_devices]))
            self._rgb_selection()
            if self._rgb_devices:
                self._message(self.rgb_status, "Algılanan RGB aygıtı: {count}", count=len(self._rgb_devices))
            else:
                self._message(self.rgb_status, "Kontrol edilebilir RGB aygıtı bulunamadı.")
        self._operation(lambda: execute([path, "--list-devices"]), finished)

    def _rgb_selection(self, *_):
        index = self.rgb_selector.get_selected()
        self._rgb_modes = self._rgb_devices[index]["modes"] if index < len(self._rgb_devices) else []
        self.rgb_mode.set_model(Gtk.StringList.new(self._rgb_modes))
        self._sync_controls()

    def _apply_rgb(self, *_):
        if not self.rgb_apply.get_sensitive():
            return
        rgba = self.rgb_color.get_rgba()
        color = "".join(f"{round(max(0, min(1, value)) * 255):02x}" for value in (rgba.red, rgba.green, rgba.blue))
        index, mode_index = self.rgb_selector.get_selected(), self.rgb_mode.get_selected()
        if index >= len(self._rgb_devices) or mode_index >= len(self._rgb_modes):
            return
        device, mode = self._rgb_devices[index], self._rgb_modes[mode_index]
        path = shutil.which("openrgb")
        if not path:
            return
        self._message(self.rgb_status, "RGB komutu gönderiliyor…")
        def finished(result):
            self._message(self.rgb_status, "OpenRGB komutu tamamlandı; ışıkları cihaz üzerinde kontrol et." if result[0] else "RGB ayarı uygulanamadı; aygıt erişimini kontrol et.")
        self._operation(lambda: execute([path, "--device", str(device["id"]), "--mode", mode, "--color", color]), finished)

    def _export(self, format):
        if not self._sample or self._closed:
            self._message(self.status, "Dışa aktarmak için ilk ölçümü bekle.")
            return
        contents = csv_text(list(self._history)) if format == "csv" else diagnostic_text(self._identity, self._sample, self._fan_channels)
        dialog = Gtk.FileDialog(title=self.tr("Ölçümleri kaydet"))
        dialog.set_initial_name(f"uzeyir-control-{datetime.now():%Y%m%d-%H%M%S}.{format}")
        def selected(dialog, result):
            try:
                file = dialog.save_finish(result)
                if not file or not file.get_path():
                    return
                path = Path(file.get_path())
                def write():
                    path.write_text(contents, encoding="utf-8")
                    return True, "", ""
                def finished(result):
                    self._message(self.status, "Dosya kaydedildi." if result[0] else "Dosya kaydedilemedi.")
                self._operation(write, finished)
            except GLib.Error:
                pass
        dialog.save(self.host, None, selected)

    def retranslate(self):
        if self._closed:
            return
        self.signal.set_tooltip_text(self.tr("Devre hareketi görseldir; fan yalnız pozitif, güncel RPM okumasında döner. Hızı ölçekli değildir."))
        self.pause_button.set_label(self.tr("Sürdür" if self._paused else "Duraklat"))
        preset_index = self.preset_selector.get_selected()
        profile_index = self.profile_selector.get_selected()
        messages = dict(self._messages)
        self.preset_selector.set_model(Gtk.StringList.new([self.tr(v[0]) for v in FAN_PRESETS.values()]))
        if preset_index < len(FAN_PRESETS):
            self.preset_selector.set_selected(preset_index)
        if self._sample:
            self._render_details()
            self.profile_selector.set_model(Gtk.StringList.new([self.tr(p) for p in self._profile_ids]))
            if profile_index < len(self._profile_ids):
                self.profile_selector.set_selected(profile_index)
            self._refresh_control_data()
        for widget, (source, values) in messages.items():
            self._message(widget, source, **values)
        self.chart.queue_draw()

    def _animations_enabled(self):
        gtk_settings = Gtk.Settings.get_default()
        return not self.settings.reduced_motion and (gtk_settings is None or gtk_settings.get_property("gtk-enable-animations"))

    def sync_motion(self):
        self.signal.sync()
        if not self._animations_enabled():
            self._cancel_motion()
            self._set_metric_values(self._targets)

    def close(self):
        self._closed = True
        self._active = False
        self.signal.active = False
        self.signal.invalidate()
        if self._source:
            GLib.source_remove(self._source)
            self._source = 0
        self._cancel_motion()
        self._history.clear()
        self._sync_controls()
