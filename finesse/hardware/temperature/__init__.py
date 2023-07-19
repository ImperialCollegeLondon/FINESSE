"""This module contains interfaces for temperature-related hardware."""
from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import cast

from pubsub import pub

from ...config import (
    NUM_TEMPERATURE_MONITOR_CHANNELS,
    TEMPERATURE_CONTROLLER_TOPIC,
    TEMPERATURE_MONITOR_TOPIC,
)
from ..serial_manager import SerialManager, make_device_factory
from .dp9800 import DP9800
from .dummy_temperature_controller import DummyTemperatureController
from .dummy_temperature_monitor import DummyTemperatureMonitor
from .tc4820 import TC4820
from .temperature_controller_base import TemperatureControllerBase
from .temperature_monitor_base import TemperatureMonitorBase

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


def get_temperature_monitor_serial_manager() -> TemperatureMonitorBase | None:
    """Get the instance of the temperature monitor."""
    global _serial_manager_dp9800
    if not _serial_manager_dp9800.is_open:
        return None
    return cast(TemperatureMonitorBase, _serial_manager_dp9800.device)


def get_hot_bb_temperature_controller_instance() -> TemperatureControllerBase | None:
    """Get the instance of the hot blackbody's temperature controller."""
    global _serial_manager_hot_bb
    if not _serial_manager_hot_bb.is_open:
        return None
    return cast(TemperatureControllerBase, _serial_manager_hot_bb.device)


def _try_get_temperatures() -> list[Decimal] | None:
    """Try to read the current temperatures from the temperature monitor.

    If the device is not connected or the operation fails, None is returned.
    """
    dev = get_temperature_monitor_serial_manager()
    if not dev:
        return None

    try:
        return dev.get_temperatures()
    except Exception as error:
        pub.sendMessage(f"serial.{TEMPERATURE_MONITOR_TOPIC}.error", error=error)
        return None


_DEFAULT_TEMPS = [Decimal("nan")] * NUM_TEMPERATURE_MONITOR_CHANNELS


def _send_temperatures() -> None:
    """Send the current temperatures (or NaNs) via pubsub."""
    temperatures = _try_get_temperatures() or _DEFAULT_TEMPS
    time = datetime.utcnow()
    pub.sendMessage(
        f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response",
        temperatures=temperatures,
        time=time,
    )


pub.subscribe(_send_temperatures, f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.request")
