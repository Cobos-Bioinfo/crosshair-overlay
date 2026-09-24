"""A live settings dialog.

Every control writes straight back into a :class:`Settings` instance and calls
the supplied callback, so the overlay updates the moment anything changes: there
is no separate "apply" step.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .config import Settings


class ColorButton(QPushButton):
    """A button that shows its current color and opens a color picker."""

    colorChanged = Signal(str)

    def __init__(self, color: str) -> None:
        super().__init__()
        self._color = color
        self.setFixedWidth(96)
        self.clicked.connect(self._pick)
        self._refresh()

    def color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = color
        self._refresh()

    def _refresh(self) -> None:
        c = QColor(self._color)
        fg = "#000000" if c.lightnessF() > 0.5 else "#FFFFFF"
        self.setStyleSheet(
            f"background-color:{self._color}; color:{fg}; border:1px solid #888; padding:4px;"
        )
        self.setText(self._color.upper())

    def _pick(self) -> None:
        chosen = QColorDialog.getColor(QColor(self._color), self, "Select color")
        if chosen.isValid():
            self._color = chosen.name()
            self._refresh()
            self.colorChanged.emit(self._color)


class SettingsDialog(QDialog):
    """Dialog exposing every crosshair property with live preview."""

    def __init__(
        self,
        settings: Settings,
        on_change: Callable[[Settings], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Crosshair settings")
        self._on_change = on_change
        self._loading = True

        # --- Cross arms ---------------------------------------------------
        self._show_lines = QCheckBox("Show cross arms")
        self._length = self._spin(1, 400)
        self._thickness = self._spin(1, 50)
        self._gap = self._spin(0, 200)
        self._t_shape = QCheckBox("T-shape (hide top arm)")

        arms = QFormLayout()
        arms.addRow(self._show_lines)
        arms.addRow("Length", self._length)
        arms.addRow("Thickness", self._thickness)
        arms.addRow("Center gap", self._gap)
        arms.addRow(self._t_shape)

        # --- Dot ----------------------------------------------------------
        self._show_dot = QCheckBox("Show center dot")
        self._dot_size = self._spin(1, 50)
        dot = QFormLayout()
        dot.addRow(self._show_dot)
        dot.addRow("Dot radius", self._dot_size)

        # --- Circle -------------------------------------------------------
        self._show_circle = QCheckBox("Show circle")
        self._circle_radius = self._spin(1, 400)
        self._circle_thickness = self._spin(1, 50)
        circle = QFormLayout()
        circle.addRow(self._show_circle)
        circle.addRow("Circle radius", self._circle_radius)
        circle.addRow("Circle thickness", self._circle_thickness)

        # --- Appearance ---------------------------------------------------
        self._color = ColorButton(settings.color)
        self._opacity = QSlider(Qt.Orientation.Horizontal)
        self._opacity.setRange(0, 100)
        self._opacity_label = QLabel()
        self._outline = QCheckBox("Outline")
        self._outline_color = ColorButton(settings.outline_color)
        self._outline_thickness = self._spin(0, 20)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self._opacity)
        opacity_row.addWidget(self._opacity_label)
        opacity_box = QWidget()
        opacity_box.setLayout(opacity_row)

        appearance = QFormLayout()
        appearance.addRow("Color", self._color)
        appearance.addRow("Opacity", opacity_box)
        appearance.addRow(self._outline)
        appearance.addRow("Outline color", self._outline_color)
        appearance.addRow("Outline thickness", self._outline_thickness)

        # --- Placement ----------------------------------------------------
        self._offset_x = self._spin(-4000, 4000)
        self._offset_y = self._spin(-4000, 4000)
        self._monitor = QComboBox()
        for i, screen in enumerate(QGuiApplication.screens()):
            g = screen.geometry()
            self._monitor.addItem(f"{i}: {screen.name()} ({g.width()}x{g.height()})")

        placement = QFormLayout()
        placement.addRow("Monitor", self._monitor)
        placement.addRow("Offset X", self._offset_x)
        placement.addRow("Offset Y", self._offset_y)

        # --- Assemble -----------------------------------------------------
        layout = QVBoxLayout(self)
        layout.addWidget(self._group("Cross arms", arms))
        layout.addWidget(self._group("Center dot", dot))
        layout.addWidget(self._group("Circle", circle))
        layout.addWidget(self._group("Appearance", appearance))
        layout.addWidget(self._group("Placement", placement))

        buttons = QHBoxLayout()
        reset = QPushButton("Reset to defaults")
        reset.clicked.connect(self._reset)
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        buttons.addWidget(reset)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        self.set_values(settings)
        self._connect()
        self._loading = False

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _spin(lo: int, hi: int) -> QSpinBox:
        box = QSpinBox()
        box.setRange(lo, hi)
        return box

    @staticmethod
    def _group(title: str, inner: QFormLayout) -> QGroupBox:
        box = QGroupBox(title)
        box.setLayout(inner)
        return box

    def _connect(self) -> None:
        for check in (
            self._show_lines,
            self._t_shape,
            self._show_dot,
            self._show_circle,
            self._outline,
        ):
            check.toggled.connect(self._emit)
        for spin in (
            self._length,
            self._thickness,
            self._gap,
            self._dot_size,
            self._circle_radius,
            self._circle_thickness,
            self._outline_thickness,
            self._offset_x,
            self._offset_y,
        ):
            spin.valueChanged.connect(self._emit)
        self._opacity.valueChanged.connect(self._emit)
        self._color.colorChanged.connect(self._emit)
        self._outline_color.colorChanged.connect(self._emit)
        self._monitor.currentIndexChanged.connect(self._emit)

    def set_values(self, s: Settings) -> None:
        """Populate every widget from ``s`` without emitting changes."""
        self._loading = True
        self._show_lines.setChecked(s.show_lines)
        self._length.setValue(s.length)
        self._thickness.setValue(s.thickness)
        self._gap.setValue(s.gap)
        self._t_shape.setChecked(s.t_shape)
        self._show_dot.setChecked(s.show_dot)
        self._dot_size.setValue(s.dot_size)
        self._show_circle.setChecked(s.show_circle)
        self._circle_radius.setValue(s.circle_radius)
        self._circle_thickness.setValue(s.circle_thickness)
        self._color.set_color(s.color)
        self._opacity.setValue(s.opacity)
        self._opacity_label.setText(f"{s.opacity}%")
        self._outline.setChecked(s.outline)
        self._outline_color.set_color(s.outline_color)
        self._outline_thickness.setValue(s.outline_thickness)
        self._offset_x.setValue(s.offset_x)
        self._offset_y.setValue(s.offset_y)
        self._monitor.setCurrentIndex(min(s.monitor, self._monitor.count() - 1))
        self._loading = False

    def current(self) -> Settings:
        """Read the current widget values into a Settings instance."""
        return Settings(
            show_lines=self._show_lines.isChecked(),
            length=self._length.value(),
            thickness=self._thickness.value(),
            gap=self._gap.value(),
            t_shape=self._t_shape.isChecked(),
            show_dot=self._show_dot.isChecked(),
            dot_size=self._dot_size.value(),
            show_circle=self._show_circle.isChecked(),
            circle_radius=self._circle_radius.value(),
            circle_thickness=self._circle_thickness.value(),
            color=self._color.color(),
            opacity=self._opacity.value(),
            outline=self._outline.isChecked(),
            outline_color=self._outline_color.color(),
            outline_thickness=self._outline_thickness.value(),
            offset_x=self._offset_x.value(),
            offset_y=self._offset_y.value(),
            monitor=max(0, self._monitor.currentIndex()),
        )

    def _emit(self) -> None:
        if self._loading:
            return
        self._opacity_label.setText(f"{self._opacity.value()}%")
        self._on_change(self.current())

    def _reset(self) -> None:
        self.set_values(Settings())
        self._emit()
