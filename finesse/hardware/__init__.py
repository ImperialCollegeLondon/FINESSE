"""This module contains code for interfacing with different hardware devices."""
import sys

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .dummy_em27_scraper import DummyEM27Scraper as EM27Scraper
    from .opus.dummy import DummyOPUSInterface as OPUSInterface
else:
    from .em27_scraper import EM27Scraper  # type: ignore
    from .opus.em27 import OPUSInterface  # type: ignore

from finesse.device_info import DeviceBaseTypeInfo, DeviceTypeInfo

from . import data_file_writer  # noqa: F401
from .plugins import load_device_types
from .plugins.stepper_motor import create_stepper_motor_serial_manager
from .plugins.temperature import (
    create_temperature_controller_serial_managers,
    create_temperature_monitor_serial_manager,
)

opus: OPUSInterface


def _get_device_type_info() -> dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]]:
    """Return info about device types grouped according to their base type."""
    base_types, device_types = load_device_types()

    # Get the base type info and sort it alphabetically by description
    base_types_info = sorted(
        (t.get_device_base_type_info() for t in base_types),
        key=lambda info: info.description,
    )

    # Preallocate dict with empty lists
    out: dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]] = {
        info: [] for info in base_types_info
    }

    # Get device type info and group by base type
    for device_type in device_types:
        out[device_type.get_device_base_type_info()].append(
            device_type.get_device_type_info()
        )

    # Sort the device types by name
    for infos in out.values():
        infos.sort(key=lambda info: info.description)

    return out


def _broadcast_device_types() -> None:
    """Broadcast the available device types via pubsub."""
    pub.sendMessage("serial.list", device_types=_get_device_type_info())


def _init_hardware():
    global opus

    opus = OPUSInterface()
    _broadcast_device_types()


def _stop_hardware():
    global opus
    del opus


pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")

scraper = EM27Scraper()
create_stepper_motor_serial_manager()
create_temperature_controller_serial_managers()
create_temperature_monitor_serial_manager()
