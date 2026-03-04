"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""

import itertools
import os
import pathlib
import tempfile
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Iterable

from PyQt6.QtCore import pyqtBoundSignal, pyqtSignal, Qt
from PyQt6.QtGui import QPen, QColor, QBrush

from zala.exceptions import ZalaException

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
    raise ZalaException("couldn't generate path")


def make_solid_pen(color: QColor, thickness: int) -> QPen:
    # Pen
    pen = QPen()
    # Reference: https://doc.qt.io/qt-6/qt.html#PenStyle-enum
    pen.setStyle(Qt.PenStyle.SolidLine)
    # Reference: https://doc.qt.io/qt-6/qt.html#PenJoinStyle-enum
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    pen.setColor(color)
    pen.setWidth(thickness)
    return pen


@contextmanager
def zala_temp_file(suffix: str = ".png") -> Iterable[pathlib.Path]:
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(tmp_fd)
    tmp_path = pathlib.Path(tmp_path)
    try:
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)


def make_brush(pattern: Qt.BrushStyle, color: QColor) -> QBrush:
    """
    https://doc.qt.io/qt-6/qbrush.html#details
    https://doc.qt.io/qt-6/qt.html#BrushStyle-enum
    """
    fill_brush = QBrush()
    fill_brush.setStyle(pattern)
    fill_brush.setColor(color)
    return fill_brush


def clamp[T: float | int](min_val: T, val: T, max_val: T) -> T:
    return max(min_val, min(val, max_val))
