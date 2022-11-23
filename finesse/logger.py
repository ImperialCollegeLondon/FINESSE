"""Set up the program's logger."""
import logging
from datetime import datetime

from platformdirs import user_log_path

from . import config


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
