"""Open every installed native module in a private compositor; never write hardware."""
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0, "/usr/share/uzeyir-control/src")
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from linux_control import APP_NAME
from linux_control.app import CSS, MainWindow
from linux_control.downloads import system_format
from linux_control.settings import Settings

assert Gtk.get_major_version() == 4 and Gtk.get_minor_version() >= 12
assert (Adw.get_major_version(), Adw.get_minor_version()) >= (1, 5)
assert Path(sys.modules["linux_control"].__file__).is_relative_to("/usr/share/uzeyir-control/src")
for source in Path('src').rglob('*'):
    if source.is_file() and '__pycache__' not in source.parts and source.suffix not in ('.pyc', '.pyo'):
        installed = Path('/usr/share/uzeyir-control/src') / source.relative_to('src')
        assert installed.read_bytes() == source.read_bytes(), source
with tempfile.TemporaryDirectory() as directory:
    app = Adw.Application(application_id="io.github.Tubix777.PackageVerification", flags=Gio.ApplicationFlags.NON_UNIQUE)
    app.register(None)
    Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    provider = Gtk.CssProvider()
    provider.load_from_string(CSS)
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 20)
    # Use the same GTK decoder as the application, including GTK 4.20+'s SVG path.
    for svg in Path('/usr/share/uzeyir-control/src/linux_control/resources').glob('*.svg'):
        paintable = Gtk.IconPaintable.new_for_file(Gio.File.new_for_path(str(svg)), 24, 1)
        snapshot = Gtk.Snapshot()
        paintable.snapshot(snapshot, 24, 24)
        assert snapshot.to_paintable(None).get_intrinsic_width() > 0, svg
    window = MainWindow(app, Settings(Path(directory) / "preferences.json"), package_format=system_format())
    window.present()
    try:
        for module in ("hardware", "wheel", "doctor"):
            for view in ("dashboard", "downloads"):
                window.select_page(module, view)
                deadline = time.monotonic() + 0.8
                context = GLib.MainContext.default()
                while time.monotonic() < deadline:
                    for _ in range(100):
                        if not context.pending():
                            break
                        context.iteration(False)
                    time.sleep(0.005)
                page = (window.downloads if view == "downloads" else window.pages)[module]
                assert page.get_mapped() and page.get_width() > 0, (module, view)
                if hasattr(page, 'scroll'):
                    assert page.scroll.get_width() >= min(page.get_width(), 1120) * 0.8, (module, view, 'content too narrow')
        assert window.get_title() == APP_NAME == "Uzeyir Control"
        assert window.downloads['doctor']._format == system_format()
        print("Installed Uzeyir Control: six native views mapped; GTK", Gtk.get_minor_version(), "Adw", Adw.get_minor_version())
    finally:
        window.on_close()
        window.destroy()
        app.quit()
