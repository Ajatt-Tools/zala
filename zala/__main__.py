"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import sys

import fire
from PyQt6.QtCore import Qt
from loguru import logger
from PyQt6.QtGui import QColor, QCursor, QIcon
from PyQt6.QtWidgets import QApplication

from zala.consts import APP_NAME, APP_LOGO_PATH
from zala.main_window import ZalaSelect, UserSelectionResult
from zala.config import ScreenshotPreviewOpts
from zala.screenshot import ZalaScreenshot, find_screen_with_cursor, repr_screen, save_screenshot
from zala.exceptions import ZalaException
from zala.take_region import ZalaTakeScreenRegion


def set_logger(verbose: bool) -> None:
    """Configure the logger level based on the verbose flag."""
    # Replace the default handler with a new one.
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(sys.stderr, level=level)


class CLI:
    """
    Screenshot taking app in PyQt.
    """

    _app: QApplication
    _scr: ZalaScreenshot

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the QApplication, set the app icon, and configure logging."""
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)
        self._app.setWindowIcon(QIcon(str(APP_LOGO_PATH)))
        self._scr = ZalaScreenshot(self._app)
        set_logger(verbose)

    def cursor_pos(self) -> None:
        """
        Print the current cursor position.
        """
        pos = QCursor.pos()

        print(f"Cursor position: {pos.x(), pos.y()}")

    def focused_screen(self) -> None:
        """
        Print the focused screen.
        """
        screens = self._scr.find_available_screens()
        print(f"Focused screen: {repr_screen(find_screen_with_cursor(screens))}")

    def screens(self) -> None:
        """
        List available screens.
        """
        for idx, screen in enumerate(self._scr.find_available_screens()):
            print(f"Screen {idx}. {repr_screen(screen)}")

    def take_screen(self, number: int | None = None, output_file_path: str | None = None) -> None:
        """
        Capture screen.
        Args:
            number: Screen number.
            output_file_path: File path where the file will be saved.
        """
        taken = self._scr.capture_screen(number)
        result = save_screenshot(taken.pixmap, output_file_path)
        if result.success:
            print(f"Screen {taken.screen.name()} saved to {result.file_path}")
        else:
            print(f"Failed to save screen {taken.screen.name()} to {result.file_path}")

    def select(
        self,
        output_file_path: str = "",
        border_thickness: int = 2,
        border_color: str = "#990000ff",
        fill_color: str = "#3c0080ff",
        outline_color: str = "#99ff0000",
        fill_brush_color: str = "#557f7f7f",
        fill_brush_pattern: str = "Dense7Pattern",
    ) -> None:
        """
        Enables an interactive selection mode
        where you may select the desired region before a screenshot is captured.
        Args:
            output_file_path: File path where the file will be saved.
            border_thickness: Thickness of the selection border in pixels.
            border_color: Rubber band border color as "#RRGGBB" or "#AARRGGBB" hex string. Alpha first.
            fill_color: Rubber band fill color as "#RRGGBB" or "#AARRGGBB" hex string. Alpha first.
            outline_color: Screen overlay outline color as "#RRGGBB" or "#AARRGGBB" hex string. Alpha first.
            fill_brush_color: Screen overlay fill color as "#RRGGBB" or "#AARRGGBB" hex string. Alpha first.
        """

        preview_opts = ScreenshotPreviewOpts(
            border_thickness=border_thickness,
            border_color=QColor(border_color),
            fill_color=QColor(fill_color),
            outline_color=QColor(outline_color),
            fill_brush_color=QColor(fill_brush_color),
            # https://doc.qt.io/qt-6/qt.html#BrushStyle-enum
            fill_brush_pattern=Qt.BrushStyle[fill_brush_pattern],
        )

        def on_finished(user_selection: UserSelectionResult) -> None:
            if not user_selection.pixmap:
                logger.info("Selection aborted")
                return

            result = save_screenshot(user_selection.pixmap, output_file_path)
            if result.success:
                print(f"Selection saved to {result.file_path}")
            else:
                print(f"Failed to save selection to {result.file_path}")

        take = ZalaTakeScreenRegion(self._scr)
        take.select_area(on_finish=on_finished, opts=preview_opts)

        self._app.exit(self._app.exec())


def main() -> None:
    """Entry point that dispatches CLI commands via python-fire."""
    try:
        fire.Fire(CLI)
    except ZalaException as e:
        print(f"Error: {e}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
