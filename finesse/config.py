"""Common constants used throughout the app."""

APP_NAME = "FINESSE"
"""A human-readable name for the app."""

APP_AUTHOR = "Imperial College London"
"""The name of the app's author (used for program data path)."""

ANGLE_PRESETS = {
    "zenith": 180.0,
    "nadir": 0.0,
    "hot_bb": 270.0,
    "cold_bb": 225.0,
    "home": 0.0,
    "park": 90.0,
}
"""Preset angles that the mirror can rotate to."""

BAUDRATES = (4800, 9600, 19200, 38400, 57600, 115200)
"""The valid baud rates for use by the GUI."""

OPUS_IP = "10.10.0.2"
"""The IP address of the machine running the OPUS software."""
