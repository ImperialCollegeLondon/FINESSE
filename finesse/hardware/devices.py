"""This module contains code for interfacing with different hardware devices."""
import logging
from importlib import import_module

from pubsub import pub

from finesse.device_info import DeviceInstanceRef

from .device_base import DeviceBase

devices: dict[DeviceInstanceRef, DeviceBase] = {}


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

    if base_type in devices:
        logging.warn(f"Replacing existing instance of device of type {base_type}")

    # If this instance also has a name (e.g. "hot_bb") then we also need to pass this as
    # an argument
    if instance.name:
        # Note that we create a new dict here so we're not modifying the original one
        params = params | {"name": instance.name}

    try:
        devices[instance] = cls.from_params(**params)
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
        device = devices.pop(instance)
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
    for device in devices.values():
        try:
            device.close()
        except Exception:
            pass


pub.subscribe(_open_device, "device.open")
pub.subscribe(_close_device, "device.close")
pub.subscribe(_on_device_error, "device.error")

pub.subscribe(_close_all_devices, "window.closed")
