"""This module contains interfaces for temperature-related hardware."""
from typing import cast

from finesse.config import TEMPERATURE_CONTROLLER_TOPIC
from finesse.device_info import DeviceInstanceRef
from finesse.hardware.devices import devices

from .temperature_controller_base import TemperatureControllerBase


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
