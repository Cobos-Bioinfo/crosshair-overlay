from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage, QPainter

from crosshair_overlay.config import Settings
from crosshair_overlay.renderer import draw_crosshair, required_extent


def _render(settings: Settings) -> QImage:
    extent = required_extent(settings)
    size = extent * 2
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    draw_crosshair(painter, QPointF(size / 2, size / 2), settings)
    painter.end()
    return image


def _opaque_pixels(image: QImage) -> int:
    return sum(
        1
        for y in range(image.height())
        for x in range(image.width())
        if image.pixelColor(x, y).alpha() > 0
    )


def test_default_crosshair_draws_pixels(qapp):
    assert _opaque_pixels(_render(Settings())) > 0


def test_dot_only_draws_pixels(qapp):
    settings = Settings(show_lines=False, show_dot=True, show_circle=False, outline=False)
    assert _opaque_pixels(_render(settings)) > 0


def test_t_shape_has_fewer_pixels_than_full_cross(qapp):
    base = Settings(show_dot=False, show_circle=False, outline=False)
    full = _opaque_pixels(_render(base))
    t_shape = _opaque_pixels(_render(Settings(**{**base.to_dict(), "t_shape": True})))
    assert 0 < t_shape < full


def test_opacity_zero_is_transparent(qapp):
    assert _opaque_pixels(_render(Settings(opacity=0))) == 0


def test_extent_grows_with_length():
    assert required_extent(Settings(length=40)) > required_extent(Settings(length=8))
