"""Set up the program's logger."""
import logging
import os
from datetime import datetime

from platformdirs import user_log_path

from . import config


def initialise_logging() -> None:
    """Configure the program's logger."""
    log_path = user_log_path(config.APP_NAME, config.APP_AUTHOR)
    log_path.mkdir(parents=True, exist_ok=True)
    filename = log_path / f"{datetime.now().strftime('%Y%m%d_%H-%M-%S')}.log"

    # Allow user to set log level with environment variable
    log_level = os.environ.get("FINESSE_LOG_LEVEL") or "INFO"
    log_level = log_level.upper()
    if not hasattr(logging, log_level):
        raise ValueError(f"Invalid log level: {log_level}")

    # Log to console and file
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(filename), logging.StreamHandler()],
    )
