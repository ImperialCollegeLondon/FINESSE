"""The main entry point to FINESSE."""
import sys

from PySide6.QtWidgets import QApplication

from .gui.main_window import MainWindow


def main() -> None:
    """Run FINESSE."""
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
