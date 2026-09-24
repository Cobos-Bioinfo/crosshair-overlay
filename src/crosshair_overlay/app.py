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

    tray: Tray | None = None
    if not args.no_tray and QSystemTrayIcon.isSystemTrayAvailable():
        tray = Tray(overlay, settings, config_path, app)
        tray.show()
    else:
        reason = "disabled with --no-tray" if args.no_tray else "no system tray detected"
        print(
            f"Running without tray ({reason}). "
            f"Edit {config_path} and restart to reconfigure.",
            file=sys.stderr,
        )

    # Let Ctrl+C from the terminal quit the app; the idle timer lets the Python
    # interpreter run often enough to deliver the signal.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    idle = QTimer()
    idle.start(200)
    idle.timeout.connect(lambda: None)

    return app.exec()
