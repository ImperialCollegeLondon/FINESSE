"""The main entry point to FINESSE."""
import logging
import sys
from datetime import datetime

from platformdirs import user_log_path
from PySide6.QtWidgets import QApplication

from . import config
from .gui.main_window import MainWindow


def initialise_logging() -> None:
    """Configure the program's logger."""
    log_path = user_log_path(config.APP_NAME, config.APP_AUTHOR)
    log_path.mkdir(parents=True, exist_ok=True)
    filename = log_path / f"{datetime.now().strftime('%Y%m%d_%H-%M-%S')}.log"

    # Log to console and file
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(filename), logging.StreamHandler()],
    )


def main() -> None:
    """Run FINESSE."""
    initialise_logging()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
