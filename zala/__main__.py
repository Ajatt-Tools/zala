"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import pathlib
import sys
import typing

import fire
from loguru import logger
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QApplication

from zala.consts import APP_NAME, APP_LOGO_PATH
from zala.main_window import ZalaSelect
from zala.screenshot import ZalaException, ZalaScreenshot, repr_screen
from zala.utils import generate_output_file_path


class ScreenshotSaveResult(typing.NamedTuple):
    success: bool
    file_path: pathlib.Path


def save_screenshot(pixmap: QPixmap, output_file_path: str | None) -> ScreenshotSaveResult:
    output_file_path = pathlib.Path(output_file_path) if output_file_path else generate_output_file_path()
    return ScreenshotSaveResult(pixmap.save(str(output_file_path)), output_file_path)


def set_logger(verbose: bool) -> None:
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
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)
        self._app.setWindowIcon(QIcon(APP_LOGO_PATH))
        self._scr = ZalaScreenshot(self._app)
        set_logger(verbose)

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

    def select(self, output_file_path: str | None = None) -> None:
        """
        Enables an interactive selection mode
        where you may select the desired region before a screenshot is captured.
        Args:
            output_file_path: File path where the file will be saved.
        """
        window = ZalaSelect(self._scr.capture_screen())
        window.showFullScreen()
        exit_code = self._app.exec()
        if window.user_selection is None:
            print("Selection aborted")
            exit_code = 1
        else:
            result = save_screenshot(window.user_selection, output_file_path)
            if result.success:
                print(f"Selection saved to {result.file_path}")
            else:
                print(f"Failed to save selection to {result.file_path}")
        self._app.exit(exit_code)


def main():
    try:
        fire.Fire(CLI)
    except ZalaException as e:
        print(f"Error: {e}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
