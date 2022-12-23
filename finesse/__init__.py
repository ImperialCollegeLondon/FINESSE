"""The main module for the FINESSE program."""
__version__ = "0.1.0"


def run() -> None:
    """Run FINESSE."""
    import sys

    from PySide6.QtWidgets import QApplication

    from . import hardware  # noqa
    from .gui.main_window import MainWindow
    from .logger import initialise_logging

    initialise_logging()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
