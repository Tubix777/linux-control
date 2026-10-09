"""One native window for monitoring, wheel controls and diagnostics."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Graphene, Gtk
from doctor.app import CSS as DOCTOR_CSS, box, label
from . import __version__
from .i18n import Translator
from .settings import Settings
from .pages.doctor import DoctorPage
from .pages.wheel import CSS as WHEEL_CSS


CSS = DOCTOR_CSS + WHEEL_CSS + """
@define-color accent_color #eeeeee;
@define-color accent_bg_color #cccccc;
@define-color accent_fg_color #101010;
@define-color window_bg_color #080808;
@define-color window_fg_color #f5f5f5;
@define-color view_bg_color #111111;
@define-color view_fg_color #f5f5f5;
@define-color card_bg_color #191919;
@define-color card_fg_color #f5f5f5;
@define-color headerbar_bg_color #080808;
@define-color headerbar_fg_color #f5f5f5;
.sidebar { background: #101010; padding: 24px 16px 20px; }
.brand { font-size: 21px; font-weight: 800; letter-spacing: -0.6px; }
.nav-button { background: transparent; border-radius: 14px; border: 1px solid transparent; padding: 15px 12px; }
.nav-button:hover { background: #232323; border-color: #383838; }
.nav-button.selected { background: #303030; border-color: #676767; }
button, switch { transition: background-color 140ms ease-out, border-color 140ms ease-out; }
window.reduce-motion * { transition: none; animation: none; }
.nav-title { font-weight: 750; font-size: 14px; }
.nav-caption { font-size: 11px; color: #b3b3b3; }
.sidebar-title { font-size: 10px; letter-spacing: 1.5px; color: #8f8f8f; font-weight: 700; }
.sidebar-footer { font-size: 11px; color: #9f9f9f; }
.page-header { font-weight: 700; }
.module-tag { background: #202020; border-radius: 8px; padding: 4px 9px; color: #bdbdbd; font-size: 11px; }
scale highlight { background: #dddddd; }
progressbar progress { background: #dddddd; }
switch:checked { background: #aaaaaa; color: #080808; }
button.suggested-action { background: #363636; color: #ffffff; border: 1px solid #6b6b6b; }
entry, searchentry { background: #202020; border-color: #414141; color: #f5f5f5; }
.heading { color: #f5f5f5; }
"""

MODULES = (
    ("hardware", "Donanım", "Sıcaklık, fan ve performans", "computer-symbolic"),
    ("wheel", "Direksiyon", "Canlı giriş ve oyun profilleri", "input-gaming-symbolic"),
    ("doctor", "Sorun Teşhisi", "Sistem taraması ve çözüm adımları", "system-search-symbolic"),
)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application, preferences=None, page_factories=None, initial="hardware", wheel_demo=False):
        super().__init__(application=application, title="Linux Control")
        self.set_default_size(1260, 880)
        self.set_size_request(960, 620)
        self.preferences = preferences or Settings()
        if self.preferences.reduced_motion:
            self.add_css_class("reduce-motion")
        self.tr = Translator(self.preferences.language)
        self._closed = False
        self.current_page = None
        self.pages = {}
        self.nav_buttons = {}
        root = box(0)
        header = Adw.HeaderBar()
        self.page_title = label("", "page-header", False)
        header.set_title_widget(self.page_title)
        tag = label("ÖN SÜRÜM", "module-tag", False)
        self.tr.bind(tag, "ÖN SÜRÜM")
        header.pack_end(tag)
        root.append(header)
        body = box(0, True)
        body.set_vexpand(True)
        sidebar = box(12)
        sidebar.set_size_request(228, -1)
        sidebar.set_hexpand(False)
        sidebar.add_css_class("sidebar")
        brand_row = box(10, True)
        resources = Path(__file__).parent / "resources"
        brand_row.append(Gtk.Image.new_from_file(str(resources / "brand.svg")))
        brand_row.append(label("Linux Control", "brand", False))
        sidebar.append(brand_row)
        tagline = label("Bilgisayarın, tek yerde.", "muted")
        self.tr.bind(tagline, "Bilgisayarın, tek yerde.")
        sidebar.append(tagline)
        section = label("ARAÇLAR", "sidebar-title")
        section.set_margin_top(22)
        self.tr.bind(section, "ARAÇLAR")
        sidebar.append(section)
        for name, title, caption, icon in MODULES:
            button = Gtk.Button()
            button.add_css_class("nav-button")
            content = box(12, True)
            image = Gtk.Image.new_from_file(str(resources / {"hardware": "computer.svg", "wheel": "wheel.svg", "doctor": "search.svg"}[name]))
            image.set_pixel_size(22)
            content.append(image)
            texts = box(4)
            texts.set_hexpand(True)
            texts.append(self.tr.bind(label(title, "nav-title", False), title))
            caption_label = label(caption, "nav-caption")
            caption_label.set_max_width_chars(25)
            texts.append(self.tr.bind(caption_label, caption))
            content.append(texts)
            button.set_child(content)
            self.tr.bind(button, title, "set_tooltip_text")
            button.connect("clicked", lambda _button, target=name: self.select_page(target))
            sidebar.append(button)
            self.nav_buttons[name] = button
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", lambda _action, _parameter, target=name: self.select_page(target))
            self.add_action(action)
        spacer = Gtk.Box(vexpand=True)
        sidebar.append(spacer)
        language_label = label("Dil", "sidebar-title")
        self.tr.bind(language_label, "Dil")
        sidebar.append(language_label)
        self.language = Gtk.DropDown.new_from_strings(["Türkçe", "English"])
        self.language.set_selected(0 if self.preferences.language == "tr" else 1)
        self.language.connect("notify::selected", self.language_changed)
        sidebar.append(self.language)
        motion_row = box(10, True)
        motion_label = label("Hareketi azalt", "sidebar-footer")
        motion_label.set_hexpand(True)
        self.tr.bind(motion_label, "Hareketi azalt")
        motion_row.append(motion_label)
        self.motion_switch = Gtk.Switch(valign=Gtk.Align.CENTER, active=self.preferences.reduced_motion)
        self.tr.bind(self.motion_switch, "Geçiş ve kaydırma animasyonlarını azalt", "set_tooltip_text")
        self.motion_switch.connect("notify::active", self.motion_changed)
        motion_row.append(self.motion_switch)
        sidebar.append(motion_row)
        footer = label("Yerel ve şeffaf", "sidebar-footer")
        self.tr.bind(footer, "Yerel ve şeffaf")
        footer.set_margin_top(16)
        sidebar.append(footer)
        sidebar.append(label(f"v{__version__}", "sidebar-footer"))
        body.append(sidebar)
        body.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self.stack = Gtk.Stack(hexpand=True, vexpand=True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(240 if self.animations_enabled() else 0)
        self.stack.set_hhomogeneous(False)
        self.stack.set_vhomogeneous(False)
        body.append(self.stack)
        root.append(body)
        self.set_content(root)
        if page_factories is None:
            from .pages.hardware import HardwarePage
            from .pages.wheel import WheelPage
            page_factories = {"hardware": HardwarePage, "wheel": WheelPage, "doctor": DoctorPage}
        for name, _, _, _ in MODULES:
            factory = page_factories[name]
            if name == "wheel" and wheel_demo:
                page = factory(self, self.tr, self.preferences, force_demo=True)
            else:
                page = factory(self, self.tr, self.preferences)
            self.pages[name] = page
            self.stack.add_named(page, name)
            page.set_active(False)
        self.tr.connect(self.retranslate)
        self.select_page(initial)
        self.connect("close-request", self.on_close)
        for index, (name, *_rest) in enumerate(MODULES, 1):
            application.set_accels_for_action("win." + name, [f"<Control>{index}"])

    def animations_enabled(self):
        settings = Gtk.Settings.get_default()
        return bool(not self.preferences.reduced_motion and settings and settings.get_property("gtk-enable-animations"))

    def select_page(self, name):
        if self._closed or name not in self.pages or name == self.current_page:
            return
        if self.current_page:
            self.pages[self.current_page].set_active(False)
            self.nav_buttons[self.current_page].remove_css_class("selected")
        self.current_page = name
        self.nav_buttons[name].add_css_class("selected")
        self.stack.set_visible_child_name(name)
        self.pages[name].set_active(True)
        self.retranslate()

    def language_changed(self, dropdown, *_):
        self.preferences.language = "tr" if dropdown.get_selected() == 0 else "en"
        self.tr.set_language(self.preferences.language)
        self.save_preferences()

    def motion_changed(self, switch, *_):
        self.preferences.reduced_motion = switch.get_active()
        if self.preferences.reduced_motion:
            self.add_css_class("reduce-motion")
        else:
            self.remove_css_class("reduce-motion")
        self.stack.set_transition_duration(240 if self.animations_enabled() else 0)
        for page in self.pages.values():
            if hasattr(page, "sync_motion"):
                page.sync_motion()
        self.save_preferences()

    def save_preferences(self):
        try:
            self.preferences.save()
        except OSError:
            # A read-only home must not stop navigation or language selection.
            pass

    def retranslate(self):
        title = next((title for name, title, *_ in MODULES if name == self.current_page), "Linux Control")
        self.page_title.set_label(self.tr(title))

    def on_close(self, *_):
        if not self._closed:
            self._closed = True
            for page in self.pages.values():
                page.close()
        return False


def save_screenshot(window, destination):
    paintable = Gtk.WidgetPaintable.new(window)
    snapshot = Gtk.Snapshot()
    paintable.snapshot(snapshot, window.get_width(), window.get_height())
    node = snapshot.to_node()
    if node is None:
        return False
    rectangle = Graphene.Rect()
    rectangle.init(0, 0, window.get_width(), window.get_height())
    texture = window.get_native().get_renderer().render_texture(node, rectangle)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    return texture.save_to_png(str(destination))


def main():
    parser = argparse.ArgumentParser(description="Linux Control native desktop application")
    parser.add_argument("--page", choices=[name for name, *_ in MODULES], default="hardware")
    parser.add_argument("--language", choices=("tr", "en"))
    parser.add_argument("--wheel-demo", action="store_true", help="Explicitly use a simulated wheel, without hardware writes")
    parser.add_argument("--screenshot", help="Render the selected page to a PNG, then exit")
    arguments = parser.parse_args()
    application = Adw.Application(application_id="io.github.Tubix777.LinuxControl", flags=Gio.ApplicationFlags.NON_UNIQUE)

    def activate(app):
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 20)
        preferences = Settings()
        if arguments.language:
            preferences.language = arguments.language
        window = MainWindow(app, preferences=preferences, initial=arguments.page, wheel_demo=arguments.wheel_demo)
        window.present()
        if arguments.screenshot:
            if arguments.page == "doctor":
                window.pages["doctor"].start_scan()
            started = GLib.get_monotonic_time()

            def render_ready():
                elapsed = (GLib.get_monotonic_time() - started) / 1_000_000
                page = window.pages[arguments.page]
                pending = getattr(page, "_busy", False) or getattr(page, "_polling", False) or getattr(page, "_scan_running", False)
                if elapsed < 3 or (pending and elapsed < 45):
                    return True
                if arguments.page == "doctor" and getattr(page, "_motion_tick_id", None) is not None and elapsed < 47:
                    return True
                okay = save_screenshot(window, arguments.screenshot)
                window.on_close()
                app.quit()
                if not okay:
                    print("UI rendering did not produce an image", file=sys.stderr)
                return False
            GLib.timeout_add(100, render_ready)
    application.connect("activate", activate)
    return application.run([])


if __name__ == "__main__":
    raise SystemExit(main())
