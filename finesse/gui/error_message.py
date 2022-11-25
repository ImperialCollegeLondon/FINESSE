"""For showing error messages."""
import logging

from PySide6.QtWidgets import QErrorMessage, QWidget


def show_error_message(parent: QWidget, msg: str) -> None:
    """Show an error message in the GUI and write to the program log."""
    # Show popup box in GUI
    QErrorMessage(parent).showMessage(msg)

    # Write to program log
    logging.error(msg)
