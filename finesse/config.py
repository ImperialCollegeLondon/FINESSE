"""Common constants used throughout the app."""
from importlib.metadata import version
from pathlib import Path

from platformdirs import user_config_path

APP_NAME = "FINESSE"
"""A human-readable name for the app."""

APP_AUTHOR = "Imperial College London"
"""The name of the app's author (used for program data path)."""

APP_VERSION = version("finesse")
"""The current version of the app."""

APP_CONFIG_PATH = user_config_path(APP_NAME, APP_AUTHOR, ensure_exists=True)
"""Path where config files will be saved."""

HARDWARE_SET_USER_PATH = APP_CONFIG_PATH / "hardware_sets"
"""Path where user-added hardware set config files will be saved."""

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

DEFAULT_SCRIPT_PATH = Path.home()
"""The default path to search for script files in."""

DEFAULT_DATA_FILE_PATH = Path.home()
"""The default path to save data files."""

EM27_HOST = "10.10.0.1"
"""The IP address or hostname of the EM27 device."""

EM27_SENSORS_URL = "http://{host}/diag_autom.htm"
"""The URL of the EM27 monitoring web server."""

EM27_SENSORS_POLL_INTERVAL = 60.0
"""Poll rate for EM27 properties."""

EM27_SENSORS_TOPIC = "em27_sensors"
"""The topic name to use for EM27 sensor-related messages."""

DECADES_HOST = "localhost"
"""The IP address or hostname of the DECADES server."""

DECADES_URL = "http://{host}/decades/livedata"
"""The URL of the DECADES sensor data endpoint."""

DECADES_POLL_INTERVAL = 60.0
"""Poll rate for DECADES sensors."""

DECADES_TOPIC = "decades"
"""The topic name to use for DECADES sensor-related messages."""

DECADES_QUERY_LIST = [
    "static_pressure",
    "gin_altitude",
    "deiced_true_air_temp_c",
]
"""List of DECADES sensor queries to make."""

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

OPUS_POLLING_INTERVAL = 1.0
"""How long to wait between polls of the EM27's status.

Note that in reality the minimum poll interval is ~2s, because that's how long the
device takes to reply. This value then determines how often we wait before even starting
a request.
"""

SPECTROMETER_TOPIC = "spectrometer"
"""The topic name to use for spectrometer-related messages."""

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

SENECA_MIN_TEMP = -80
"""The default minimum temperature limit of the Seneca K107 device."""

SENECA_MAX_TEMP = 105
"""The default maximum temperature limit of the Seneca K107 device."""

SENECA_MIN_MILLIVOLT = 4
"""The default minimum voltage output (millivolts) of the Seneca K107 device."""

SENECA_MAX_MILLIVOLT = 20
"""The default maximum voltage output (millivolts) of the Seneca K107 device."""

TIME_TOPIC = "time"
"""The topic name to use for time-related messages."""

TIME_NTP_HOST = "localhost"
"""The IP address or hostname of the NTP time server."""

TIME_NTP_VERSION = 3
"""The version of the NTP protocol to use."""

TIME_NTP_PORT = "ntp"
"""The port to use for NTP queries."""

TIME_NTP_TIMEOUT = 5.0
"""The timeout for NTP queries."""
