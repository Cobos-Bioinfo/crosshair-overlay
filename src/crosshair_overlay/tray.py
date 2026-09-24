"""System tray icon: toggle, open settings, reload config, quit."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from .config import Settings, load_settings, save_settings
from .overlay import Overlay
from .renderer import draw_crosshair
from .settings_dialog import SettingsDialog


def make_icon() -> QIcon:
    """Build the tray icon by drawing a small crosshair (no asset files)."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    glyph = Settings(
        length=14,
        thickness=4,
        gap=7,
        dot_size=3,
        color="#FFFFFF",
        outline=True,
        outline_thickness=2,
    )
    draw_crosshair(painter, QPointF(32, 32), glyph)
    painter.end()
    return QIcon(pixmap)


class Tray(QSystemTrayIcon):
    """Tray icon that owns the settings dialog and config persistence."""

    def __init__(
        self,
        overlay: Overlay,
        settings: Settings,
        config_path: Path,
        app: QApplication,
    ) -> None:
        super().__init__(make_icon())
        self._overlay = overlay
        self._settings = settings
        self._config_path = config_path
        self._app = app
        self._dialog: SettingsDialog | None = None
        self.setToolTip("Crosshair Overlay")

        menu = QMenu()
        self._toggle_action = QAction("Hide crosshair", menu)
        self._toggle_action.triggered.connect(self._toggle)
        settings_action = QAction("Settings…", menu)
        settings_action.triggered.connect(self._open_settings)
        reload_action = QAction("Reload config", menu)
        reload_action.triggered.connect(self._reload)
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit)

        menu.addAction(self._toggle_action)
        menu.addAction(settings_action)
        menu.addAction(reload_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # left click
            self._toggle()

    def _toggle(self) -> None:
        if self._overlay.isVisible():
            self._overlay.hide()
            self._toggle_action.setText("Show crosshair")
        else:
            self._overlay.show()
            self._toggle_action.setText("Hide crosshair")

    def _apply(self, settings: Settings) -> None:
        self._settings = settings
        self._overlay.apply(settings)
        save_settings(settings, self._config_path)

    def open_settings(self) -> None:
        """Show the settings dialog (public entry point)."""
        if self._dialog is None:
            self._dialog = SettingsDialog(self._settings, self._apply)
        else:
            self._dialog.set_values(self._settings)
        self._dialog.show()
        self._dialog.raise_()
        self._dialog.activateWindow()

    def _open_settings(self) -> None:
        self.open_settings()

    def _reload(self) -> None:
        self._settings = load_settings(self._config_path)
        self._overlay.apply(self._settings)
        if self._dialog is not None:
            self._dialog.set_values(self._settings)

    def _quit(self) -> None:
        self._app.quit()
