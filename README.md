<p align="center">
<img height="100px" src="https://raw.githubusercontent.com/Ajatt-Tools/zala/refs/heads/main/doc/logo.svg" alt="Project logo">
</p>

# Zala

[![PyPi](https://img.shields.io/pypi/v/zala?style=for-the-badge)](https://pypi.org/project/Zala/)
[![Chat](https://img.shields.io/badge/chat-join-green?style=for-the-badge&logo=Telegram&logoColor=green)](https://ajatt.top/blog/join-our-community.html)
[![Support](https://img.shields.io/badge/support-developer-orange?style=for-the-badge&logo=Patreon&logoColor=orange)](https://ajatt.top/blog/donating-to-tatsumoto.html)

<img align="right" height="100px" src="https://github.com/user-attachments/assets/eed00245-984a-4d68-a53b-5ed384dc1cc1" alt="ZALA Z-16">

Zala is a screenshot tool designed to capture images of your desktop.
It has options to capture a specific region of the screen.
Built using PyQt,
Zala can be integrated into Python projects as a dependency.

If you're looking for a standalone program to
create screenshots and don't plan to integrate it into a PyQt project,
consider using [maim](https://github.com/naelstrof/maim).
Maim is written in a more efficient language.

## Install

Install using [pipx](https://pipx.pypa.io/stable/) from [pypi](https://pypi.org/project/zala/).

```bash
pipx install zala
```

## Python usage

Zala can be integrated into PyQt6 projects as a library.
The example below shows how to capture a screenshot and let the user select a region.

```python
import sys

from PyQt6.QtWidgets import QApplication
from zala.main_window import ZalaSelect
from zala.screenshot_preview import UserSelectionResult
from zala.screenshot import ZalaScreenshot


def main() -> None:
    app = QApplication(sys.argv)
    scr = ZalaScreenshot(app)

    def on_selection_finished(result: UserSelectionResult) -> None:
        if result.pixmap:
            result.pixmap.save("screenshot.png")
        app.quit()

    sel = ZalaSelect(scr.capture_screen())
    sel.selection_finished.connect(on_selection_finished)
    sel.showFullScreen()
    app.exec()


if __name__ == "__main__":
    main()
```

## Bash examples

Take a region of the screen.

```bash
zala select
```

Verbose mode.

```bash
zala select -v
```

Show commands.

```bash
zala
```
