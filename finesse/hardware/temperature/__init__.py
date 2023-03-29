"""This module contains interfaces for temperature-related hardware."""
from functools import partial

from ...config import TEMPERATURE_CONTROLLER_TOPIC
from ..serial_manager import SerialManager, make_device_factory
from .dummy_temperature_controller import DummyTemperatureController
from .tc4820 import TC4820

_serial_manager_hot_bb: SerialManager
_serial_manager_cold_bb: SerialManager


def _create_serial_manager(name: str) -> SerialManager:
    return SerialManager(
        f"{TEMPERATURE_CONTROLLER_TOPIC}.{name}",
        make_device_factory(
            partial(TC4820, name), partial(DummyTemperatureController, name)
        ),
    )


def create_temperature_controller_serial_managers() -> None:
    """Create SerialManagers for the cold and hot black body temperature controllers."""
    global _serial_manager_cold_bb, _serial_manager_hot_bb
    _serial_manager_hot_bb = _create_serial_manager("hot_bb")
    _serial_manager_cold_bb = _create_serial_manager("cold_bb")
