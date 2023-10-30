"""Common constants used throughout the app."""
from importlib.metadata import version
from pathlib import Path

APP_NAME = "FINESSE"
"""A human-readable name for the app."""

APP_AUTHOR = "Imperial College London"
"""The name of the app's author (used for program data path)."""

APP_VERSION = version("finesse")
"""The current version of the app."""

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

NUM_TEMPERATURE_MONITOR_CHANNELS = 8
"""The number of temperature channels for temperature monitors."""

DUMMY_DEVICE_PORT = "Dummy"
"""The port name to display for dummy serial devices."""

DEFAULT_SCRIPT_PATH = Path.home()
"""The default path to search for script files in."""

DEFAULT_DATA_FILE_PATH = Path.home()
"""The default path to save data files."""

EM27_URL = "http://10.10.0.1/diag_autom.htm"
"""The URL of the EM27 monitoring web server."""

EM27_SENSORS_POLL_INTERVAL = 60.0
"""Poll rate for EM27 properties."""

EM27_SENSORS_TOPIC = "em27"
"""The topic name to use for EM27 sensor-related messages."""

DEFAULT_HTTP_TIMEOUT = 2.0
"""How long to wait for a response from a server for."""

STEPPER_MOTOR_TOPIC = "stepper_motor"
"""The topic name to use for stepper motor-related messages."""

TEMPERATURE_MONITOR_TOPIC = "temperature_monitor"
"""The topic name to use for temperature monitor-related messages."""

TEMPERATURE_CONTROLLER_TOPIC = "temperature_controller"
"""The topic name to use for temperature controller-related messages."""

OPUS_IP = "10.10.0.2"
"""The IP address of the machine running the OPUS software."""

TEMPERATURE_CONTROLLER_POLL_INTERVAL = 2
"""Number of seconds between temperature controller device reads."""

TEMPERATURE_MONITOR_POLL_INTERVAL = 2
"""Number of seconds between temperature monitoring device reads."""

TEMPERATURE_PLOT_TIME_RANGE = 900
"""Range of time axis on blackbody temperature plot, in seconds."""

TEMPERATURE_MONITOR_HOT_BB_IDX = 6
"""Position of the hot blackbody on the temperature monitoring device."""

TEMPERATURE_MONITOR_COLD_BB_IDX = 7
"""Position of the cold blackbody on the temperature monitoring device."""
