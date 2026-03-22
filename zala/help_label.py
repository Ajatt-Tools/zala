"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

from typing import Self

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QLabel, QWidget

SELECT_CONTROLS = {
    "Wheel": "zoom",
    "Shift+Wheel": "rotate",
    "Right+drag": "pan",
    "Left+drag": "select",
    "I": "hide",
    "Q": "quit",
}
HELP_TEXT = " ｜ ".join(f"<b>{binding}</b>: {action}" for binding, action in SELECT_CONTROLS.items())
LABEL_CSS = """
QLabel {
    background-color: rgba(0, 0, 0, 180);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-family: "Noto Sans Mono", "Noto Sans Mono CJK JP", "Noto Mono", "DejaVu Sans Mono", "DejaVuSansMono Nerd Font",
        "DejaVuSansMono Nerd Font Mono", "Droid Sans Mono", "DroidSansMono Nerd Font", "DroidSansMono Nerd Font Mono",
        "Fantasque Sans Mono", "Hack Nerd Font Mono", "JetBrainsMono Nerd Font", "JetBrainsMono Nerd Font Mono",
        "JetBrainsMono NF", "JetBrainsMono NFM", "JetBrainsMono NFP", "JetBrainsMonoNL Nerd Font",
        "JetBrainsMonoNL Nerd Font Mono", "JetBrainsMonoNL NF", "JetBrainsMonoNL NFM", "JetBrainsMonoNL NFP",
        "Knack Nerd Font Mono", "Lucida Console", "Miriam Mono CLM", "Nimbus Mono PS", "Liberation Mono",
        "PixelCarnageMono", "Adwaita Mono", "Courier New", Consolas, Courier, monospace;
}
"""


class ZalaHelpLabel(QLabel):
    """A help label widget that displays keyboard/mouse controls at the bottom of the viewport."""

    _bottom_padding: int = 10

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the help label with default text and styling."""
        super().__init__(parent)
        self.setText(HELP_TEXT)
        self.setStyleSheet(LABEL_CSS)

    def position_help_label(self, viewport: QWidget | None) -> Self:
        """
        Position the help label at the bottom center of the viewport.
        https://doc.qt.io/qt-6/qabstractscrollarea.html#viewport
        """
        if viewport is None:
            return self
        viewport_rect = viewport.rect()
        label_size = self.sizeHint()
        self.move(
            QPoint(
                (viewport_rect.width() - label_size.width()) // 2,
                (viewport_rect.height() - label_size.height() - self._bottom_padding),
            )
        )
        return self

    def setup_help_label(self, viewport: QWidget, is_visible: bool = True) -> Self:
        """
        Create and configure the help label at the bottom of the viewport.
        https://doc.qt.io/qt-6/qwidget.html#adjustSize
        """
        self.show()
        self.adjustSize()
        self.position_help_label(viewport)
        self.setVisible(is_visible)
        return self

    def toggle_visibility(self) -> Self:
        """Toggle the visibility of the help label."""
        self.setVisible(not self.isVisible())
        return self
