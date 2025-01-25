"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import itertools
import pathlib
import sys
import time

import fire
from PyQt6.QtWidgets import QApplication

from zala.screenshot import ZalaException, repr_screen, ZalaScreenshot


def generate_output_file_path() -> pathlib.Path:
    if not pathlib.Path.home().is_dir():
        raise ZalaException("home directory doesn't exist")
    for idx in itertools.count(start=int(time.time())):
        path = pathlib.Path.home().joinpath(f"screenshot_{idx}.png")
        if not path.is_file():
            return path


class CLI:
    """
    Screenshot taking app in PyQt.
    """

    def screens(self) -> None:
        """
        List available screens.
        """
        app = QApplication(sys.argv)
        scr = ZalaScreenshot(app)
        for idx, screen in enumerate(scr.find_available_screens()):
            print(f"Screen {idx}. {repr_screen(screen)}")

    def take_screen(self, number: int | None = None, output_file_path: str | None = None):
        """
        Capture screen.
        Args:
            number: Screen number.
            output_file_path: File path where the file will be saved.
        """
        app = QApplication(sys.argv)
        scr = ZalaScreenshot(app)
        pixmap = scr.capture_screen(number)
        output_file_path = pathlib.Path(output_file_path) if output_file_path else generate_output_file_path()
        if pixmap.save(str(output_file_path)):
            print(f"Screenshot saved to {output_file_path}")
        else:
            print(f"Failed to save screenshot to {output_file_path}")

    def select(self):
        """
        Enables an interactive selection mode
        where you may select the desired region before a screenshot is captured.
        """
        raise NotImplementedError
        # app = QApplication(sys.argv)
        # window = ZalaApp()
        # window.showFullScreen()
        # app.exit(app.exec())


def main():
    try:
        fire.Fire(CLI)
    except ZalaException as e:
        print(f"Error: {e}.")


if __name__ == "__main__":
    main()
