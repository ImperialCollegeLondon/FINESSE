"""This module contains code for interfacing with different hardware devices."""
import sys
from decimal import Decimal

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .plugins.em27.dummy_opus_interface import DummyOPUSInterface as OPUSInterface
else:
    from .plugins.em27.opus_interface import OPUSInterface  # type: ignore

from datetime import datetime

from finesse.config import NUM_TEMPERATURE_MONITOR_CHANNELS, TEMPERATURE_MONITOR_TOPIC

from . import data_file_writer  # noqa: F401
from .device import get_device_types
from .plugins.temperature import get_temperature_monitor_instance
from .plugins.temperature.temperature_monitor_base import TemperatureSequence

_opus: OPUSInterface


def _broadcast_device_types() -> None:
    """Broadcast the available device types via pubsub."""
    pub.sendMessage("device.list", device_types=get_device_types())


def _try_get_temperatures() -> TemperatureSequence | None:
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
    temperatures = _try_get_temperatures() or _DEFAULT_TEMPS
    time = datetime.utcnow()
    pub.sendMessage(
        f"device.{TEMPERATURE_MONITOR_TOPIC}.data.response",
        temperatures=temperatures,
        time=time,
    )


pub.subscribe(_send_temperatures, f"device.{TEMPERATURE_MONITOR_TOPIC}.data.request")


def _init_hardware():
    global _opus

    _opus = OPUSInterface()

    _broadcast_device_types()


def _stop_hardware():
    global _opus
    del _opus


pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")
