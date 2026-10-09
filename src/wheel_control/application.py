from __future__ import annotations

import sys

import gi

gi.require_version("Adw", "1")
from gi.repository import Adw, Gio

from .ui import WheelWindow, load_css


class WheelApplication(Adw.Application):
    def __init__(self, force_demo: bool = False) -> None:
        super().__init__(
            application_id="io.github.tubix777.WheelControl",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.force_demo = force_demo
        self.window: WheelWindow | None = None

    def do_activate(self) -> None:
        if self.window is None:
            Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            load_css()
            self.window = WheelWindow(self, force_demo=self.force_demo)
        self.window.present()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    force_demo = "--demo" in argv
    argv = [argument for argument in argv if argument != "--demo"]
    try:
        return WheelApplication(force_demo=force_demo).run(argv)
    except KeyboardInterrupt:
        return 130
