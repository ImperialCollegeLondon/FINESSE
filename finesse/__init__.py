"""The main module for the FROG program."""

from finesse.config import APP_VERSION

__version__ = APP_VERSION


def run() -> None:
    """Run FROG."""
    import sys

    from PySide6.QtWidgets import QApplication

    # This must be done before our own modules are imported
    from finesse.logger import initialise_logging

    initialise_logging()

    from finesse import hardware  # noqa
    from finesse.gui.main_window import MainWindow

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
