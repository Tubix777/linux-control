"""Native GTK 4 interface. All diagnostics run outside the UI thread."""
from __future__ import annotations

import argparse
import threading
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Graphene, Gtk
from . import __version__
from .core import Finding, check_app, list_flatpaks, scan


CSS = """
window { background: #080808; color: #f5f5f5; }
.hero { font-size: 30px; font-weight: 800; letter-spacing: -1px; }
.muted { color: #b3b3b3; }
.eyebrow { color: #d0d0d0; font-weight: 700; font-size: 12px; }
.card { background: #191919; border: 1px solid #383838; border-radius: 16px; padding: 18px; }
.card-title { font-size: 16px; font-weight: 700; }
.pill { border-radius: 10px; padding: 4px 9px; font-size: 11px; font-weight: 700; }
.ok { background: #2a2a2a; color: #dedede; }
.warning { background: #353535; color: #ffffff; border: 1px solid #777777; }
.critical { background: #454545; color: #ffffff; border: 1px solid #ededed; }
.info, .unknown { background: #272727; color: #d5d5d5; }
button { background-image: none; color: #f5f5f5; }
.primary { background: #363636; color: #ffffff; border: 1px solid #6b6b6b; border-radius: 12px; padding: 12px 22px; font-weight: 700; }
.primary:hover { background: #474747; }
.primary:active { background: #292929; }
.soft { background: #262626; border: 1px solid #3a3a3a; border-radius: 12px; padding: 10px 16px; }
.soft:hover { background: #353535; }
.soft:active { background: #202020; }
dropdown > button { background: #2a2a2a; border: 1px solid #414141; }
popover contents { background: #191919; color: #f5f5f5; }
listview row:selected { background: #414141; color: #ffffff; }
selection { background: #555555; color: #ffffff; }
:focus-visible { outline-color: #b8b8b8; }
.summary { background: #202020; border: 1px solid #343434; border-radius: 16px; padding: 18px; }
.evidence { color: #c5c5c5; font-family: monospace; font-size: 12px; }
.metric { font-size: 32px; font-weight: 800; }
.metric-bar trough { background: #333333; min-height: 6px; border: 0; border-radius: 8px; }
.metric-bar progress { background: #dddddd; min-height: 6px; border: 0; border-radius: 8px; }
headerbar { background: #080808; box-shadow: none; }
"""
STATUS = {"ok": "İyi", "warning": "Dikkat", "critical": "Önemli", "info": "Bilgi", "unknown": "Kontrol edilemedi"}


def label(text: str, css: str = "", wrap: bool = True) -> Gtk.Label:
    item = Gtk.Label(label=text, xalign=0, wrap=wrap)
    if css:
        item.add_css_class(css)
    return item


def box(spacing: int = 8, horizontal: bool = False) -> Gtk.Box:
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL if horizontal else Gtk.Orientation.VERTICAL, spacing=spacing)


class Window(Adw.ApplicationWindow):
    def __init__(self, application, screenshot: str | None = None):
        super().__init__(application=application, title="Fedora Doctor")
        self.set_default_size(1040, 820)
        self.apps = []
        self.folder = None
        self.screenshot = screenshot
        self._busy = False
        self._motion_tick_id = None
        self._auto_scroll = False
        self._scroll_started = None
        self._scroll_from = 0.0
        self._cards = []
        self._fade_started = {}
        self._revealed = set()
        root = box(0)
        header = Adw.HeaderBar()
        header.set_title_widget(label("Fedora Doctor", "card-title"))
        root.append(header)
        scroll = self.scroll = Gtk.ScrolledWindow(vexpand=True)
        content = self.content = box(22)
        scroll.get_vadjustment().connect("value-changed", self.viewport_changed)
        scroll.get_vadjustment().connect("changed", self.viewport_changed)
        wheel = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        wheel.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        wheel.connect("scroll", self.manual_scroll)
        scroll.add_controller(wheel)
        pointer = Gtk.GestureClick.new()
        pointer.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        pointer.connect("pressed", lambda *_: self.interrupt_auto_scroll())
        scroll.add_controller(pointer)
        keys = Gtk.EventControllerKey.new()
        keys.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        keys.connect("key-pressed", self.navigation_key)
        scroll.add_controller(keys)
        self.connect("close-request", self.close_motion)
        for method in (content.set_margin_top, content.set_margin_bottom,
                       content.set_margin_start, content.set_margin_end):
            method(28)
        scroll.set_child(content)
        root.append(scroll)
        self.set_content(root)
        hero = box(8)
        hero.append(label("BİLGİSAYARINI ANLA", "eyebrow"))
        hero.append(label("Sorun ne? Birlikte bakalım.", "hero"))
        hero.append(label("Linux kontrolleri, anlaşılır açıklamalar ve uygulanabilir adımlar.", "muted"))
        content.append(hero)
        actions = box(12, True)
        self.scan_button = Gtk.Button(label="Sistemi tara")
        self.scan_button.add_css_class("primary")
        self.scan_button.connect("clicked", lambda *_: self.start_scan())
        actions.append(self.scan_button)
        self.spinner = Gtk.Spinner(visible=False)
        actions.append(self.spinner)
        actions.append(label("Yerel çalışır · Sistem ayarlarını değiştirmez", "muted"))
        content.append(actions)
        self.summary = label("Henüz tarama yapılmadı. İlk kontrol birkaç saniye sürer.", "summary")
        content.append(self.summary)
        app_panel = box(10)
        app_panel.add_css_class("card")
        app_panel.append(label("Bir uygulamada sorun mu var?", "card-title"))
        app_panel.append(label("Kurulu Flatpak uygulamasını seç. İstersen erişemediği klasörü de kontrol et.", "muted"))
        app_controls = box(10, True)
        self.app_model = Gtk.StringList.new(["Uygulamalar yükleniyor…"])
        self.dropdown = Gtk.DropDown(model=self.app_model, hexpand=True)
        self.dropdown.set_tooltip_text("Kontrol edilecek Flatpak uygulaması")
        app_controls.append(self.dropdown)
        self.folder_button = Gtk.Button(label="Klasör seç")
        self.folder_button.add_css_class("soft")
        self.folder_button.connect("clicked", self.choose_folder)
        app_controls.append(self.folder_button)
        self.app_button = Gtk.Button(label="Uygulamayı kontrol et")
        self.app_button.add_css_class("soft")
        self.app_button.set_sensitive(False)
        self.app_button.connect("clicked", self.start_app)
        app_controls.append(self.app_button)
        app_panel.append(app_controls)
        self.folder_label = label("Klasör seçimi isteğe bağlıdır.", "muted")
        app_panel.append(self.folder_label)
        content.append(app_panel)
        self.results = box(12)
        content.append(self.results)
        self.results.append(label("Bulgular burada görünecek.", "muted"))
        content.append(label(f"Fedora Doctor {__version__} · İlk çalışan prototip · Günlükler dışarı gönderilmez", "muted"))
        self.present()
        self.background(list_flatpaks, self.set_apps)

    def background(self, task, callback):
        def worker():
            try:
                value = task()
            except Exception:
                value = None
            GLib.idle_add(callback, value)
        threading.Thread(target=worker, daemon=True).start()

    def set_apps(self, apps):
        self.apps = apps or []
        self.app_model.splice(0, self.app_model.get_n_items(),
            [f"{name} · {'kişisel' if scope == 'user' else scope}" for _, name, scope in self.apps]
            or ["Kurulu Flatpak uygulaması bulunamadı"])
        self.dropdown.set_sensitive(bool(self.apps) and not self._busy)
        self.app_button.set_sensitive(bool(self.apps) and not self._busy)
        if self.screenshot:
            self.start_scan()
        return False

    def choose_folder(self, *_):
        dialog = Gtk.FileDialog(title="Kontrol edilecek klasör")
        dialog.select_folder(self, None, self.folder_chosen)

    def folder_chosen(self, dialog, result):
        try:
            selected = dialog.select_folder_finish(result)
            path = selected.get_path()
            if not path:
                self.folder_label.set_label("Yalnız yerel klasörler kontrol edilebilir.")
                return
            self.folder = path
            self.folder_button.set_label("Klasörü değiştir")
            self.folder_label.set_label("Seçilen klasör: " + selected.get_basename())
        except GLib.Error:
            pass

    def busy(self, value):
        self._busy = value
        self.scan_button.set_sensitive(not value)
        self.app_button.set_sensitive(not value and bool(self.apps))
        self.dropdown.set_sensitive(not value and bool(self.apps))
        self.folder_button.set_sensitive(not value)
        self.spinner.set_visible(value)
        self.spinner.set_spinning(value)

    def start_scan(self):
        self.cancel_motion()
        self.busy(True)
        self.summary.set_label("Sistem kontrol ediliyor…")
        self.background(scan, self.show_findings)

    def start_app(self, *_):
        index = self.dropdown.get_selected()
        if index >= len(self.apps):
            return
        app_id, name, scope = self.apps[index]
        folder = self.folder
        self.cancel_motion()
        self.busy(True)
        self.summary.set_label(name + " kontrol ediliyor…")
        self.background(lambda: check_app(app_id, scope, folder), self.show_findings)

    def show_findings(self, findings):
        self.cancel_motion()
        self.busy(False)
        while self.results.get_first_child():
            self.results.remove(self.results.get_first_child())
        if findings is None:
            findings = [Finding("Tarama tamamlanamadı", "unknown", "Bir kontrol sırasında hata oluştu. Tekrar taramayı deneyebilirsin.")]
        alerts = sum(item.status in ("warning", "critical") for item in findings)
        unknown = sum(item.status == "unknown" for item in findings)
        self.summary.set_label(f"{len(findings)} kontrol tamamlandı · {alerts} dikkat gerektiren bulgu · {unknown} kontrol edilemeyen alan")
        order = {"critical": 0, "warning": 1, "unknown": 2, "ok": 3, "info": 4}
        def finding_order(item):
            priority = 0 if item.status in ("critical", "warning") else 1 if item.metric is not None else 2
            return priority, order[item.status]
        for item in sorted(findings, key=finding_order):
            card = box(9)
            card.add_css_class("card")
            heading = box(10, True)
            title = label(item.title, "card-title")
            title.set_hexpand(True)
            heading.append(title)
            pill = label(STATUS[item.status], "pill")
            pill.add_css_class(item.status)
            heading.append(pill)
            card.append(heading)
            if item.metric is not None:
                metric_row = box(12, True)
                metric_row.append(label(f"%{item.metric:g}", "metric"))
                metric_row.append(label(item.metric_label, "muted"))
                card.append(metric_row)
                meter = Gtk.ProgressBar(fraction=max(0.0, min(1.0, item.metric / 100)))
                meter.add_css_class("metric-bar")
                card.append(meter)
            card.append(label(item.explanation))
            details = box(8)
            details.append(label(item.certainty, "muted"))
            for evidence in item.evidence:
                details.append(label(evidence, "evidence"))
            if item.steps:
                details.append(label("Ne yapabilirsin?", "card-title"))
                for index, step in enumerate(item.steps, 1):
                    details.append(label(f"{index}. {step}"))
            expander = Gtk.Expander(label="Kanıt ve çözüm adımları")
            expander.set_child(details)
            card.append(expander)
            self.results.append(card)
            self._cards.append(card)
        if self.animations_enabled():
            for card in self._cards:
                card.set_opacity(0)
        self._auto_scroll = True
        self.queue_motion()
        if self.screenshot:
            GLib.timeout_add(1800, self.save_screenshot)
        return False

    def animations_enabled(self):
        settings = Gtk.Settings.get_default()
        return bool(settings and settings.get_property("gtk-enable-animations"))

    def queue_motion(self, *_):
        if self._motion_tick_id is None and self._cards:
            self._motion_tick_id = self.add_tick_callback(self.motion_frame)

    def viewport_changed(self, *_):
        if len(self._revealed) < len(self._cards):
            self.queue_motion()

    def interrupt_auto_scroll(self):
        self._auto_scroll = False
        self._scroll_started = None

    def manual_scroll(self, *_):
        self.interrupt_auto_scroll()
        return False

    def navigation_key(self, _controller, key, _code, _state):
        if key in (Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Page_Up, Gdk.KEY_Page_Down,
                   Gdk.KEY_Home, Gdk.KEY_End, Gdk.KEY_space):
            self.interrupt_auto_scroll()
        return False

    def cancel_motion(self):
        if self._motion_tick_id is not None:
            self.remove_tick_callback(self._motion_tick_id)
            self._motion_tick_id = None
        for card in self._cards:
            card.set_opacity(1)
        self._cards = []
        self._fade_started = {}
        self._revealed = set()
        self._auto_scroll = False
        self._scroll_started = None

    def close_motion(self, *_):
        self.cancel_motion()
        return False

    def motion_frame(self, _widget, clock):
        adjustment = self.scroll.get_vadjustment()
        allocated, bounds = self.results.compute_bounds(self.content)
        # Tick callbacks precede layout. Wait for the new result cards to allocate.
        if not allocated or not self._cards or self._cards[0].get_height() <= 0:
            return True
        now = clock.get_frame_time()
        target = max(adjustment.get_lower(), min(bounds.get_y() - 24,
                     adjustment.get_upper() - adjustment.get_page_size()))
        if not self.animations_enabled():
            if self._auto_scroll:
                adjustment.set_value(target)
            for index, card in enumerate(self._cards):
                card.set_opacity(1)
                self._revealed.add(index)
            self._auto_scroll = False
            self._motion_tick_id = None
            return False
        if self._auto_scroll:
            if self._scroll_started is None:
                self._scroll_started = now
                self._scroll_from = adjustment.get_value()
            progress = min(1.0, max(0.0, (now - self._scroll_started) / 1050000))
            eased = 1 - (1 - progress) ** 3
            adjustment.set_value(self._scroll_from + (target - self._scroll_from) * eased)
            if progress >= 1:
                self._auto_scroll = False
        top = adjustment.get_value()
        bottom = top + adjustment.get_page_size()
        visible_order = 0
        fading = False
        for index, card in enumerate(self._cards):
            if index in self._revealed:
                continue
            found, card_bounds = card.compute_bounds(self.content)
            visible = found and card_bounds.get_y() < bottom - 8 and card_bounds.get_y() + card_bounds.get_height() > top + 8
            if visible and index not in self._fade_started:
                self._fade_started[index] = now + min(visible_order * 70000, 210000)
                visible_order += 1
            if index in self._fade_started:
                progress = min(1.0, max(0.0, (now - self._fade_started[index]) / 420000))
                card.set_opacity(1 - (1 - progress) ** 3)
                if progress >= 1:
                    self._revealed.add(index)
                else:
                    fading = True
        if self._auto_scroll or fading:
            return True
        self._motion_tick_id = None
        return False

    def save_screenshot(self):
        paintable = Gtk.WidgetPaintable.new(self)
        snapshot = Gtk.Snapshot()
        paintable.snapshot(snapshot, self.get_width(), self.get_height())
        node = snapshot.to_node()
        if node is not None:
            rectangle = Graphene.Rect()
            rectangle.init(0, 0, self.get_width(), self.get_height())
            texture = self.get_native().get_renderer().render_texture(node, rectangle)
            texture.save_to_png(self.screenshot)
        self.get_application().quit()
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--screenshot", help="Save a rendered UI image after a real read-only scan, then exit")
    arguments = parser.parse_args()
    application = Adw.Application(application_id="io.github.fedoradoctor.App", flags=Gio.ApplicationFlags.NON_UNIQUE)
    def activate(app):
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Window(app, arguments.screenshot)
    application.connect("activate", activate)
    application.run([])
