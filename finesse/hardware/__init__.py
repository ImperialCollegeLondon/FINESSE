"""This module contains code for interfacing with different hardware devices."""
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from pubsub import pub

from finesse.config import NUM_TEMPERATURE_MONITOR_CHANNELS, TEMPERATURE_MONITOR_TOPIC
from finesse.hardware import data_file_writer  # noqa: F401
from finesse.hardware.plugins.temperature import get_temperature_monitor_instance
from finesse.hardware.plugins.time import get_time_instance


def _try_get_time() -> float | None:
    """Try to read the current time from the time source.

    iF the device is not connected or the operation fails, None is returned.
    """
    dev = get_time_instance()
    if not dev:
        return None

    try:
        return dev.get_time()
    except Exception as error:
        dev.send_error_message(error)
        return None


def _try_get_temperatures() -> Sequence | None:
    """Try to read the current temperatures from the temperature monitor.

    If the device is not connected or the operation fails, None is returned.
    """
    dev = get_temperature_monitor_instance()
    if not dev:
        return None

    try:
        return dev.get_temperatures()
    except Exception as error:
        dev.send_error_message(error)
        return None


_DEFAULT_TEMPS = [Decimal("nan")] * NUM_TEMPERATURE_MONITOR_CHANNELS


def _send_temperatures() -> None:
    """Send the current temperatures (or NaNs) via pubsub."""
    temperatures = _try_get_temperatures()
    if temperatures is None:
        temperatures = _DEFAULT_TEMPS

    # Get time from the time source.
    epoch_time = _try_get_time()
    if epoch_time is None:
        # On failure, set time to the UNIX epoch.
        epoch_time = 0.0
    time = datetime.fromtimestamp(epoch_time, tz=UTC)

    pub.sendMessage(
        f"device.{TEMPERATURE_MONITOR_TOPIC}.data.response",
        temperatures=temperatures,
        time=time,
    )


pub.subscribe(_send_temperatures, f"device.{TEMPERATURE_MONITOR_TOPIC}.data.request")
