"""Code for FINESSE's documentation viewer window."""
import os
import webbrowser

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QAction, QDesktopServices

from finesse.logger import get_log_path


class LogOpen(QAction):
    """A menu option for opening the current log file."""

    def __init__(self, parent: QObject) -> None:
        """Create a menu item for opening the current log file.

        Args:
            parent: the menu on which to place the menu item
        """
        super().__init__("Open log", parent)
        self.triggered.connect(self.open_log)

    def open_log(self) -> None:
        """Opens the current log file."""
        self.path = os.path.realpath(get_log_path())
        self.files = [
            f"{self.path}\{x}" for x in os.listdir(self.path) if x.endswith(".log")
        ]
        self.log = max(self.files, key=os.path.getctime)
        webbrowser.open(self.log)


class LogLocationOpen(QAction):
    """A menu option for opening the log file folder location."""

    def __init__(self, parent: QObject) -> None:
        """Create a menu item for opening the log file folder location.

        Args:
            parent: the menu on which to place the menu item
        """
        super().__init__("Open file location", parent)
        self.triggered.connect(self.open_file_location)

    def open_file_location(self) -> None:
        """Opens the log file folder location."""
        self.path = os.path.realpath(get_log_path())
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.path))
