"""Native navigation and async downloads without network or hardware writes."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from linux_control.app import MainWindow
from linux_control.settings import Settings
from linux_control.downloads import bundled_release


class FakePage(Gtk.Box):
    def __init__(self, host, translator, settings):
        super().__init__()
        self.host, self.active, self.closed = host, False, False

    def set_active(self, active):
        self.active = active

    def sync_motion(self):
        pass

    def close(self):
        self.closed = True


@unittest.skipUnless(Gtk.init_check() and Gdk.Display.get_default() is not None, "Private GTK display required")
class DownloadPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Adw.init()
        cls.app = Adw.Application(application_id="io.github.Tubix777.LinuxControl.DownloadTests", flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        preferences = Settings(Path(self.temp.name) / "preferences.json")
        self.window = MainWindow(self.app, preferences, {name: FakePage for name in ("hardware", "wheel", "doctor")})

    def tearDown(self):
        self.window.on_close()
        self.window.destroy()
        self.temp.cleanup()

    def drain(self, predicate, timeout=1):
        deadline = time.monotonic() + timeout
        context = GLib.MainContext.default()
        while time.monotonic() < deadline:
            while context.pending():
                context.iteration(False)
            if predicate():
                return
            time.sleep(.003)
        self.fail("Download callback did not arrive")

    def test_each_sidebar_download_button_opens_its_own_page_and_returns(self):
        pages = dict(self.window.pages)
        for module in ("hardware", "wheel", "doctor"):
            self.window.download_buttons[module].emit("clicked")
            self.assertEqual(self.window.current_page, module)
            self.assertEqual(self.window.current_view, "downloads")
            self.assertEqual(self.window.stack.get_visible_child_name(), module + "-downloads")
            self.assertFalse(any(page.active for page in pages.values()))
            self.assertTrue(self.window.downloads[module]._active)
            self.window.select_page(module)
            self.assertTrue(pages[module].active)
            self.assertFalse(self.window.downloads[module]._active)
            self.assertEqual(self.window.pages, pages)

    def test_language_changes_preserve_package_format_and_do_not_accumulate_bindings(self):
        page = self.window.downloads["hardware"]
        page.format_selector.set_selected(page.release.formats.index("deb"))
        count = len(self.window.tr._bindings)
        for language in ("en", "tr", "en", "tr"):
            self.window.tr.set_language(language)
            self.assertEqual(page._format, "deb")
            self.assertTrue(all("apt install" in command for command in page.commands))
        self.assertEqual(len(self.window.tr._bindings), count)

    def test_network_worker_does_not_block_navigation_or_write_to_the_host(self):
        entered, release = threading.Event(), threading.Event()
        thread_ids = []
        def loader(module):
            thread_ids.append(threading.get_ident())
            entered.set()
            release.wait(1)
            return bundled_release(module)
        page = self.window.downloads["wheel"]
        page.loader = loader
        try:
            page.refresh()
            self.assertTrue(entered.wait(.3))
            self.window.select_page("doctor")
            reached = []
            GLib.idle_add(lambda: reached.append(True) or GLib.SOURCE_REMOVE)
            self.drain(lambda: bool(reached))
            self.assertEqual(self.window.current_page, "doctor")
            self.assertTrue(page._busy)
            self.assertNotIn(threading.get_ident(), thread_ids)
        finally:
            release.set()
            self.drain(lambda: not page._busy)

    def test_offline_refresh_keeps_existing_download_links(self):
        page = self.window.downloads["hardware"]
        before = page.release
        def failed(_module):
            raise OSError("offline")
        page.loader = failed
        page.refresh()
        self.drain(lambda: not page._busy)
        self.assertIs(page.release, before)
        self.assertTrue(page.asset_buttons)
        self.assertIn("alınamadı", page.status.get_label())

    def test_callback_after_close_is_inert(self):
        page = self.window.downloads["doctor"]
        before = page.release
        generation = page._generation
        self.window.on_close()
        page.received(generation, bundled_release("hardware"))
        self.assertIs(page.release, before)
        self.assertTrue(all(download._closed for download in self.window.downloads.values()))
        self.window.select_downloads("hardware")
        self.assertEqual(self.window.current_page, "hardware")
