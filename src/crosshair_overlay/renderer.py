"""Vector rendering of the crosshair with QPainter.

Everything is drawn from primitives (lines, an ellipse, a ring) so the reticle
stays crisp at any size and needs no image assets. Each element is painted twice
when an outline is enabled: once slightly larger in the outline color, then again
in the main color on top.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen

from .config import Settings


def required_extent(s: Settings) -> int:
    """Maximum distance in pixels from the center that any element reaches.

    Used to size the overlay window so the crosshair always fits with a little
    padding to spare.
    """
    extent = 0
    if s.show_lines:
        extent = max(extent, s.gap + s.length + s.thickness)
    if s.show_dot:
        extent = max(extent, s.dot_size)
    if s.show_circle:
        extent = max(extent, s.circle_radius + s.circle_thickness)
    if s.outline:
        extent += s.outline_thickness
    return extent + 2


def _color(hex_str: str, opacity: int) -> QColor:
    color = QColor(hex_str)
    if not color.isValid():
        color = QColor("#000000")
    color.setAlpha(max(0, min(255, round(opacity / 100 * 255))))
    return color


def draw_crosshair(painter: QPainter, center: QPointF, s: Settings) -> None:
    """Paint the crosshair described by ``s`` centered at ``center``."""
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    main = _color(s.color, s.opacity)
    outline = _color(s.outline_color, s.opacity)
    extra = s.outline_thickness if s.outline else 0
    cx, cy = center.x(), center.y()

    def paint_lines(color: QColor, pad: int) -> None:
        pen = QPen(color)
        pen.setWidth(max(1, s.thickness + 2 * pad))
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        gap, length = s.gap, s.length
        painter.drawLine(QPointF(cx + gap, cy), QPointF(cx + gap + length, cy))
        painter.drawLine(QPointF(cx - gap, cy), QPointF(cx - gap - length, cy))
        painter.drawLine(QPointF(cx, cy + gap), QPointF(cx, cy + gap + length))
        if not s.t_shape:
            painter.drawLine(QPointF(cx, cy - gap), QPointF(cx, cy - gap - length))

    def paint_circle(color: QColor, pad: int) -> None:
        pen = QPen(color)
        pen.setWidth(max(1, s.circle_thickness + 2 * pad))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, s.circle_radius, s.circle_radius)

    def paint_dot(color: QColor, pad: int) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        radius = s.dot_size + pad
        painter.drawEllipse(center, radius, radius)

    # Outline pass: draw every enabled element enlarged, in the outline color.
    if s.outline and extra > 0:
        if s.show_circle:
            paint_circle(outline, extra)
        if s.show_lines:
            paint_lines(outline, extra)
        if s.show_dot:
            paint_dot(outline, extra)

    # Main pass on top.
    if s.show_circle:
        paint_circle(main, 0)
    if s.show_lines:
        paint_lines(main, 0)
    if s.show_dot:
        paint_dot(main, 0)
