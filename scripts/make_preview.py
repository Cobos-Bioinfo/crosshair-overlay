"""Render a strip of example crosshair presets to ``docs/preview.png``.

Run with ``uv run python scripts/make_preview.py``. Uses Qt's offscreen backend
so it works without a display.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path  # noqa: E402

from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from crosshair_overlay.config import Settings  # noqa: E402
from crosshair_overlay.renderer import draw_crosshair  # noqa: E402

PRESETS: list[tuple[str, Settings]] = [
    ("Classic", Settings(color="#00FF00")),
    ("Dot", Settings(show_lines=False, dot_size=4, color="#00E5FF")),
    ("T-shape", Settings(t_shape=True, length=12, color="#FFD400")),
    (
        "Circle + dot",
        Settings(show_lines=False, show_circle=True, circle_radius=16, dot_size=3, color="#FF4081"),
    ),
    (
        "Sniper",
        Settings(
            length=26, thickness=2, gap=8, show_circle=True, circle_radius=6, dot_size=2,
            color="#FFFFFF",
        ),
    ),
]

CELL_W, CELL_H = 150, 170
BACKGROUND = QColor("#1e1f22")


def main() -> None:
    QApplication([])
    width = CELL_W * len(PRESETS)
    image = QImage(width, CELL_H, QImage.Format.Format_ARGB32)
    image.fill(BACKGROUND)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    font = QFont()
    font.setPointSize(10)
    painter.setFont(font)

    for i, (name, settings) in enumerate(PRESETS):
        if i > 0:
            painter.setPen(QColor("#33353a"))
            painter.drawLine(i * CELL_W, 12, i * CELL_W, CELL_H - 12)
        center = QPointF(i * CELL_W + CELL_W / 2, 72)
        draw_crosshair(painter, center, settings)
        painter.setPen(QColor("#c8c8c8"))
        painter.drawText(
            i * CELL_W, CELL_H - 34, CELL_W, 22, Qt.AlignmentFlag.AlignHCenter, name
        )
    painter.end()

    out = Path(__file__).resolve().parent.parent / "docs" / "preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
