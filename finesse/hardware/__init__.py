"""This module contains code for interfacing with different hardware devices."""
import logging
import sys
from importlib import import_module

from pubsub import pub

if "--dummy-em27" in sys.argv:
    from .dummy_em27_scraper import DummyEM27Scraper as EM27Scraper
    from .opus.dummy import DummyOPUSInterface as OPUSInterface
else:
    from .em27_scraper import EM27Scraper  # type: ignore
    from .opus.em27 import OPUSInterface  # type: ignore

from finesse.device_info import DeviceBaseTypeInfo, DeviceInstanceRef, DeviceTypeInfo

from . import data_file_writer  # noqa: F401
from .device_base import DeviceBase
from .plugins import load_device_types
from .plugins.stepper_motor import create_stepper_motor_serial_manager
from .plugins.temperature import (
    create_temperature_controller_serial_managers,
    create_temperature_monitor_serial_manager,
)

_opus: OPUSInterface
_devices: dict[DeviceInstanceRef, DeviceBase] = {}


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
    pub.sendMessage("device.list", device_types=_get_device_type_info())


def _open_device(
    module: str, class_name: str, instance: DeviceInstanceRef, params: dict[str, str]
) -> None:
    """Open the specified device type.

    Args:
        module: The module the device type's class resides in
        class_name: The name of the device type's class
        instance: The instance that this device will be when opened
        params: Device parameters
    """
    # Assume this is safe because module and class_name will not be provided directly by
    # the user
    cls: DeviceBase = getattr(import_module(module), class_name)

    base_type = cls.get_device_base_type_info().name
    logging.info(f"Opening device of type {base_type}: {class_name}")

    if base_type in _devices:
        logging.warn(f"Replacing existing instance of device of type {base_type}")

    # If this instance also has a name (e.g. "hot_bb") then we also need to pass this as
    # an argument
    if instance.name:
        # Note that we create a new dict here so we're not modifying the original one
        params = params | {"name": instance.name}

    try:
        _devices[instance] = cls.from_params(**params)
    except Exception as error:
        logging.error(f"Failed to open {base_type} device: {str(error)}")
        pub.sendMessage("device.error", instance=instance, error=error)
    else:
        logging.info("Opened device")

        # Signal that device is now open
        pub.sendMessage(f"device.opened.{instance.topic}")


def _close_device(instance: DeviceInstanceRef) -> None:
    """Close the device referred to by instance."""
    try:
        device = _devices.pop(instance)
    except KeyError:
        # There is no instance of this type of device (this can happen if an error
        # occurs during opening)
        return

    logging.info(f"Closing device of type {instance.base_type}")
    device.close()
    pub.sendMessage(f"device.closed.{instance.topic}")


def _on_device_error(instance: DeviceInstanceRef, error: Exception) -> None:
    """Treat all errors as fatal on device error."""
    _close_device(instance)


def _close_all_devices() -> None:
    """Attempt to close all devices, ignoring errors."""
    for device in _devices.values():
        try:
            device.close()
        except Exception:
            pass


def _init_hardware():
    global _opus

    _opus = OPUSInterface()

    _broadcast_device_types()


def _stop_hardware():
    global _opus
    del _opus

    # Try to close all devices if window closes unexpectedly
    _close_all_devices()


pub.subscribe(_open_device, "device.open")
pub.subscribe(_close_device, "device.close")
pub.subscribe(_on_device_error, "device.error")

pub.subscribe(_init_hardware, "window.opened")
pub.subscribe(_stop_hardware, "window.closed")

scraper = EM27Scraper()
create_stepper_motor_serial_manager()
create_temperature_controller_serial_managers()
create_temperature_monitor_serial_manager()
