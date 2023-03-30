"""For showing error messages."""
import logging
from typing import Optional

from PySide6.QtWidgets import QMessageBox, QWidget


def show_error_message(parent: Optional[QWidget], msg: str) -> None:
    """Show an error message in the GUI and write to the program log."""
    # Show popup box in GUI
    msg_box = QMessageBox(
        QMessageBox.Icon.Critical,
        "An error has occurred",
        msg,
        QMessageBox.StandardButton.Ok,
        parent,
    )
    msg_box.exec()

    # Write to program log
    logging.error(msg)
