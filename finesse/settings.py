"""A module with a single settings object for the program settings."""
from PySide6.QtCore import QSettings

from .config import APP_AUTHOR, APP_NAME

settings = QSettings(APP_AUTHOR, APP_NAME)
"""Contains the program settings for FINESSE."""
