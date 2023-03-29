"""The main module for the FINESSE program."""
__version__ = "0.1.0"


def run() -> None:
    """Run FINESSE."""
    import sys

    from PySide6.QtWidgets import QApplication

    # This must be done before our own modules are imported
    from .logger import initialise_logging

    initialise_logging()

    from . import hardware  # noqa
    from .gui.main_window import MainWindow

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
