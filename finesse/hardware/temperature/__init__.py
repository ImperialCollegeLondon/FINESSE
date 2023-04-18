"""This module contains interfaces for temperature-related hardware."""
from functools import partial
from typing import cast

from ...config import TEMPERATURE_CONTROLLER_TOPIC, TEMPERATURE_MONITOR_TOPIC
from ..serial_manager import SerialManager, make_device_factory
from .dp9800 import DP9800
from .dummy_temperature_controller import DummyTemperatureController
from .dummy_temperature_monitor import DummyTemperatureMonitor
from .tc4820 import TC4820
from .temperature_controller_base import TemperatureControllerBase

_serial_manager_hot_bb: SerialManager
_serial_manager_cold_bb: SerialManager
_serial_manager_dp9800: SerialManager


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


def create_temperature_monitor_serial_manager() -> None:
    """Create SerialManagers for the temperaturemonitor."""
    global _serial_manager_dp9800
    _serial_manager_dp9800 = SerialManager(
        TEMPERATURE_MONITOR_TOPIC,
        make_device_factory(DP9800, DummyTemperatureMonitor),
    )


def get_hot_bb_temperature_controller_instance() -> TemperatureControllerBase:
    """Get the instance of the hot blackbody's temperature controller."""
    global _serial_manager_hot_bb
    return cast(TemperatureControllerBase, _serial_manager_hot_bb.device)
