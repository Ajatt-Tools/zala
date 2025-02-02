"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import itertools
import pathlib
import time
from collections.abc import Callable

from PyQt6.QtCore import pyqtBoundSignal, pyqtSignal

from zala.screenshot import ZalaException

MISSING = object()


def qconnect(signal: Callable | pyqtSignal | pyqtBoundSignal, func: Callable) -> None:
    """Helper to work around type checking not working with signal.connect(func)."""
    signal.connect(func)  # type: ignore


def q_emit(signal: Callable | pyqtSignal | pyqtBoundSignal, value=MISSING) -> None:
    """Helper to work around type checking not working with signal.emit(func)."""
    if value is not MISSING:
        signal.emit(value)  # type: ignore
    else:
        signal.emit()  # type: ignore


def generate_output_file_path() -> pathlib.Path:
    """
    Generate an unused file name in the home directory to save a screenshot to.
    """
    if not pathlib.Path.home().is_dir():
        raise ZalaException("home directory doesn't exist")
    for idx in itertools.count(start=int(time.time())):
        path = pathlib.Path.home().joinpath(f"screenshot_{idx}.png")
        if not path.is_file():
            return path
