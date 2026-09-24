"""Application entry point and command-line interface."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

from . import __version__
from .config import Settings, default_config_path, load_settings, save_settings


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="crosshair",
        description="Lightweight, cross-platform crosshair overlay for games.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to the config file (default: per-user config directory).",
    )
    parser.add_argument(
        "--settings",
        action="store_true",
        help="Open the settings window on launch.",
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Run without a system tray icon (edit the config file to reconfigure).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Write default settings to the config file and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"crosshair-overlay {__version__}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    config_path: Path = args.config or default_config_path()

    if args.reset:
        save_settings(Settings(), config_path)
        print(f"Default settings written to {config_path}")
        return 0

    # Import Qt lazily so --help/--version/--reset work without a display.
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon

    from .overlay import Overlay
    from .settings_dialog import SettingsDialog
    from .tray import Tray

    app = QApplication([sys.argv[0]])
    app.setApplicationName("Crosshair Overlay")
    app.setApplicationDisplayName("Crosshair Overlay")
    app.setQuitOnLastWindowClosed(False)

    settings = load_settings(config_path)
    if not config_path.exists():
        save_settings(settings, config_path)

    overlay = Overlay(settings)
    overlay.show()

    def apply_and_save(new_settings: Settings) -> None:
        overlay.apply(new_settings)
        save_settings(new_settings, config_path)

    tray: Tray | None = None
    if not args.no_tray and QSystemTrayIcon.isSystemTrayAvailable():
        tray = Tray(overlay, settings, config_path, app)
        tray.show()

    # Keep a reference so the dialog is not garbage collected.
    dialog: SettingsDialog | None = None

    if tray is not None:
        if args.settings:
            tray.open_settings()
    elif args.no_tray and not args.settings:
        # Fully headless: overlay only, controlled via the config file.
        print(
            f"Running without tray (disabled with --no-tray). Edit {config_path} and "
            "restart, or pass --settings to open the settings window.",
            file=sys.stderr,
        )
    else:
        # No tray available (or --settings asked without a tray): the settings
        # window becomes the control surface, and closing it quits the app.
        if not args.settings:
            print(
                "No system tray detected (common on WSL and minimal Linux desktops). "
                "Opened the settings window instead; close it to quit. For a tray icon "
                "and a reliable in-game overlay, run on Windows or an X11 desktop.",
                file=sys.stderr,
            )
        dialog = SettingsDialog(settings, apply_and_save)
        dialog.finished.connect(lambda *_: app.quit())
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    # Let Ctrl+C from the terminal quit the app; the idle timer lets the Python
    # interpreter run often enough to deliver the signal.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    idle = QTimer()
    idle.start(200)
    idle.timeout.connect(lambda: None)

    return app.exec()
