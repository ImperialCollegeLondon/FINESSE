"""A module with a single settings object for the program settings."""
from platformdirs import user_config_path
from PySide6.QtCore import QSettings

from finesse.config import APP_AUTHOR, APP_NAME

# We use platformdirs to choose the path for config file because Qt seems to use a
# slightly different scheme (at least on Linux)
_config_dir = user_config_path(APP_NAME, APP_AUTHOR, ensure_exists=True)
settings = QSettings(str(_config_dir / "settings.conf"))
"""Contains the program settings for FINESSE."""
