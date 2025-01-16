"""
Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
"""
import sys

from PyQt6.QtWidgets import QMainWindow, QApplication

from zala.consts import APP_NAME


class ZalaApp(QMainWindow):
    """
    The main window that is being shown when the app is called.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        self.initUI()

    def initUI(self):
        self.setMinimumSize(640, 480)





def main():
    app = QApplication(sys.argv)
    window = ZalaApp()
    window.show()
    app.exit(app.exec())


if __name__ == "__main__":
    main()

