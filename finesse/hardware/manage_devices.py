"""This module contains code for interfacing with different hardware devices."""
import logging
from importlib import import_module
from typing import TypeVar, cast

from pubsub import pub

from finesse.device_info import DeviceInstanceRef

from .device import Device

_devices: dict[DeviceInstanceRef, Device] = {}

_T = TypeVar("_T", bound=Device)


def get_device_instance(base_type: type[_T], name: str | None = None) -> _T | None:
    """Get the instance of the device of type base_type with an optional name.

    If there is no device matching these parameters, None is returned.
    """
    key = DeviceInstanceRef(base_type.get_device_base_type_info().name, name)

    try:
        return cast(_T, _devices[key])
    except KeyError:
        return None


def _open_device(
    class_name: str, instance: DeviceInstanceRef, params: dict[str, str]
) -> None:
    """Open the specified device type.

    Args:
        class_name: The name of the device type's class
        instance: The instance that this device will be when opened
        params: Device parameters
    """
    module, _, class_name = class_name.rpartition(".")

    # Assume this is safe because module and class_name will not be provided directly by
    # the user
    cls: Device = getattr(import_module(module), class_name)

    logging.info(f"Opening device of type {instance.base_type}: {class_name}")

    if instance in _devices:
        logging.warn(f"Replacing existing instance of device of type {instance.topic}")

    # If this instance also has a name (e.g. "hot_bb") then we also need to pass this as
    # an argument
    if instance.name:
        # Note that we create a new dict here so we're not modifying the original one
        params = params | {"name": instance.name}

    try:
        _devices[instance] = cls(**params)  # type: ignore[operator]
    except Exception as error:
        logging.error(f"Failed to open {instance.topic} device: {str(error)}")
        pub.sendMessage(
            f"device.error.{instance.topic}", instance=instance, error=error
        )
    else:
        logging.info("Opened device")

        # Signal that device is now open
        pub.sendMessage(f"device.opened.{instance.topic}")


def _try_close_device(device: Device) -> None:
    """Try to close a device and send a message on success.

    If an exception is raised it is logged without being re-raised.
    """
    logging.info(f"Closing device of type {device.__class__}")

    try:
        device.close()
    except Exception as ex:
        logging.warn(f"Error while closing {device.__class__}: {ex!s}")
    else:
        topic = device.get_device_base_type_info().name
        if device.name:
            topic += f".{device.name}"
        pub.sendMessage(f"device.closed.{topic}")


def _close_device(instance: DeviceInstanceRef) -> None:
    """Close the device referred to by instance."""
    try:
        _try_close_device(_devices.pop(instance))
    except KeyError:
        # There is no instance of this type of device, so do nothing
        pass


def _on_device_error(instance: DeviceInstanceRef, error: Exception) -> None:
    """Treat all errors as fatal on device error."""
    _close_device(instance)


def _close_all_devices() -> None:
    """Attempt to close all devices, ignoring errors."""
    for device in _devices.values():
        _try_close_device(device)
    _devices.clear()


pub.subscribe(_open_device, "device.open")
pub.subscribe(_close_device, "device.close")
pub.subscribe(_on_device_error, "device.error")

pub.subscribe(_close_all_devices, "window.closed")
