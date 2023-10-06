"""This module contains interfaces for temperature-related hardware."""
from typing import cast

from finesse.config import TEMPERATURE_CONTROLLER_TOPIC, TEMPERATURE_MONITOR_TOPIC
from finesse.device_info import DeviceInstanceRef
from finesse.hardware.devices import devices

from .temperature_controller_base import TemperatureControllerBase
from .temperature_monitor_base import TemperatureMonitorBase


def get_temperature_controller_instance(name: str) -> TemperatureControllerBase | None:
    """Get the current temperature controller instance specified by name or None.

    Args:
        name: The name of the temperature controller instance (e.g. "hot_bb")
    """
    try:
        return cast(
            TemperatureControllerBase,
            devices[DeviceInstanceRef(TEMPERATURE_CONTROLLER_TOPIC, name)],
        )
    except KeyError:
        return None


def get_temperature_monitor_instance() -> TemperatureMonitorBase | None:
    """Get the current temperature monitor device or None."""
    try:
        return cast(
            TemperatureMonitorBase,
            devices[DeviceInstanceRef(TEMPERATURE_MONITOR_TOPIC)],
        )
    except KeyError:
        return None
