"""The transparent, click-through, always-on-top overlay window.

Input transparency is achieved with Qt's ``WindowTransparentForInput`` flag,
which works across X11, Windows and macOS without any platform-specific code, so
mouse and keyboard events pass straight through to the game underneath.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QGuiApplication, QPainter, QPaintEvent, QScreen
from PySide6.QtWidgets import QWidget

from .config import Settings
from .renderer import draw_crosshair, required_extent


class Overlay(QWidget):
    """A tiny frameless window that paints the crosshair at the screen center."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowTitle("Crosshair Overlay")
        self._reposition()

    def apply(self, settings: Settings) -> None:
        """Adopt new settings and repaint immediately."""
        self._settings = settings
        self._reposition()
        self.update()

    def _target_screen(self) -> QScreen:
        screens = QGuiApplication.screens()
        idx = self._settings.monitor
        if 0 <= idx < len(screens):
            return screens[idx]
        return QGuiApplication.primaryScreen()

    def _reposition(self) -> None:
        s = self._settings
        extent = required_extent(s)
        size = extent * 2
        geo = self._target_screen().geometry()
        cx = geo.x() + geo.width() // 2 + s.offset_x
        cy = geo.y() + geo.height() // 2 + s.offset_y
        self.setGeometry(cx - extent, cy - extent, size, size)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        center = QPointF(self.width() / 2, self.height() / 2)
        draw_crosshair(painter, center, self._settings)
        painter.end()
