"""Provides base classes for all types of devices.

The Device class is the top-level base class from which all devices ultimately inherit.
Concrete classes for devices must not inherit directly from this class, but instead
should inherit from a device base class (defined by passing is_base_type to the class
constructor).
"""
from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

from decorator import decorate
from pubsub import pub

from finesse.device_info import (
    DeviceBaseTypeInfo,
    DeviceInstanceRef,
    DeviceParameter,
    DeviceTypeInfo,
)

from .plugins import load_all_plugins

_base_types: set[type[Device]] = set()
"""Registry of device base types."""

_device_types: set[type[Device]] = set()
"""Registry of concrete device types."""


def get_device_types() -> dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]]:
    """Return info about device types grouped according to their base type."""
    # Ensure all base types and device types have been registered
    load_all_plugins()

    # Get the base type info and sort it alphabetically by description
    base_types_info = sorted(
        (t.get_device_base_type_info() for t in _base_types),
        key=lambda info: info.description,
    )

    # Preallocate dict with empty lists
    out: dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]] = {
        info: [] for info in base_types_info
    }

    # Get device type info and group by base type
    for device_type in _device_types:
        out[device_type.get_device_base_type_info()].append(
            device_type.get_device_type_info()
        )

    # Sort the device types by name
    for infos in out.values():
        infos.sort(key=lambda info: info.description)

    return out


class AbstractDevice(ABC):
    """An abstract base class for devices."""

    _device_base_type_info: DeviceBaseTypeInfo
    """Information about the device's base type."""
    _device_description: str
    """A human-readable name."""
    _device_parameters: list[DeviceParameter] | None = None
    """Possible parameters that this device type accepts.

    The key represents the parameter name and the value is a list of possible values.
    """

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the device."""

    @classmethod
    def add_device_parameters(cls, *parameters: DeviceParameter) -> None:
        """Add extra parameters for this device class."""
        if cls._device_parameters is None:
            cls._device_parameters = []

        cls._device_parameters.extend(parameters)

    @classmethod
    def get_device_parameters(cls) -> list[DeviceParameter]:
        """Get the parameters for this device class."""
        return cls._device_parameters or []

    @classmethod
    def get_device_base_type_info(cls) -> DeviceBaseTypeInfo:
        """Get information about the base type for this device type."""
        return cls._device_base_type_info

    @classmethod
    def get_device_type_info(cls) -> DeviceTypeInfo:
        """Get information about this device type."""
        return DeviceTypeInfo(
            cls._device_description,
            cls.get_device_parameters(),
            f"{cls.__module__}.{cls.__name__}",
        )


class Device(AbstractDevice):
    """A base class for device types.

    This class is the base class for device base types and (indirectly) concrete device
    type classes. Unlike AbstractDevice, it provides an __init_subclass__ method to
    initialise the its subclasses differently depending on whether or not they are
    defined as device base types or not.
    """

    def __init_subclass__(cls, is_base_type: bool = False, **kwargs: Any) -> None:
        """Initialise a device type class.

        Args:
            is_base_type: Whether this class represents a device base type
        """
        # If it is a base class, we initialise it as such
        if is_base_type:
            cls._init_base_type(**kwargs)
            return

        # If it is not, it should inherit from one
        if not set(cls.__bases__).intersection(_base_types):
            raise ValueError(
                f"Class {cls.__name__} must be a device base type or inherit from one."
            )

        # And we initialise it as a concrete device class
        cls._init_device_type(**kwargs)

    @classmethod
    def _init_base_type(
        cls,
        name: str,
        description: str,
        names_short: Sequence[str] = (),
        names_long: Sequence[str] = (),
        **kwargs,
    ) -> None:
        super().__init_subclass__(**kwargs)

        # Store metadata about this base class
        cls._device_base_type_info = DeviceBaseTypeInfo(
            name, description, names_short, names_long
        )

        # Add the class to the registry of base types
        _base_types.add(cls)

    @classmethod
    def _init_device_type(
        cls,
        description: str,
        **kwargs,
    ) -> None:
        super().__init_subclass__(**kwargs)

        # Set device description for this class
        cls._device_description = description

        # Add the class to the registry of device types
        _device_types.add(cls)

    def __init__(self, name: str | None = None) -> None:
        """Create a new Device.

        Args:
            name: A name to distinguish devices of the same type.
        """
        self.topic = f"device.{self._device_base_type_info.name}"
        """The name of the root pubsub topic on which this device will broadcast."""

        self.name = name
        """The (optional) name of this device to use in pubsub messages."""

        self._subscriptions: list[tuple[Callable, str]] = []
        """Store of wrapped functions which are subscribed to pubsub messages."""

        if not self._device_base_type_info.names_short:
            if name:
                raise RuntimeError(
                    "Name provided for device which cannot accept names."
                )
            return

        if name not in self._device_base_type_info.names_short:
            raise RuntimeError("Invalid name given for device")

        self.topic += f".{name}"

    def close(self) -> None:
        """Close the device and clear any pubsub subscriptions."""
        for sub in self._subscriptions:
            pub.unsubscribe(*sub)

    def get_instance_ref(self) -> DeviceInstanceRef:
        """Get the DeviceInstanceRef corresponding to this device."""
        return DeviceInstanceRef(self._device_base_type_info.name, self.name)

    def send_error_message(self, error: Exception) -> None:
        """Send an error message for this device."""
        # Write to log
        traceback_str = "".join(traceback.format_exception(error))
        logging.error(f"Error with device {self.topic}: {traceback_str}")

        # Send pubsub message
        instance = self.get_instance_ref()
        pub.sendMessage(
            f"device.error.{instance.topic}",
            instance=instance,
            error=error,
        )

    def pubsub_errors(self, func: Callable) -> Callable:
        """Catch exceptions and broadcast via pubsub.

        Args:
            func: The function to wrap
        """

        def wrapped(func, *args, **kwargs):
            try:
                func(*args, **kwargs)
            except Exception as error:
                self.send_error_message(error)

        return decorate(func, wrapped)

    def pubsub_broadcast(
        self, func: Callable, success_topic_suffix: str, *kwarg_names: str
    ) -> Callable:
        """Broadcast success or failure of function via pubsub.

        If the function returns without error, the returned values are sent as arguments
        to the success_topic message.

        Args:
            func: The function to wrap
            success_topic_suffix: The topic name on which to broadcast function results
            kwarg_names: The names of each of the returned values
        """

        def wrapped(func, *args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as error:
                self.send_error_message(error)
            else:
                # Convert result to a tuple of the right size
                if result is None:
                    result = ()
                elif not isinstance(result, tuple):
                    result = (result,)

                # Make sure we have the right number of return values
                assert len(result) == len(kwarg_names)

                # Send message with arguments
                pub.sendMessage(
                    f"{self.topic}.{success_topic_suffix}",
                    **dict(zip(kwarg_names, result)),
                )

        return decorate(func, wrapped)

    def subscribe(
        self,
        func: Callable,
        topic_name_suffix: str,
        success_topic_suffix: str | None = None,
        *kwarg_names: str,
    ) -> None:
        """Subscribe to a pubsub topic using the pubsub_* helper functions.

        Errors will be broadcast with the message "device.error.{THIS_INSTANCE}". If
        success_topic_suffix is provided, a message will also be sent on success (see
        pubsub_broadcast).

        Args:
            func: Function to subscribe to
            topic_name_suffix: The suffix of the topic to subscribe to
            success_topic_suffix: The topic name on which to broadcast function results
            kwarg_names: The names of each of the returned values
        """
        if success_topic_suffix:
            wrapped_func = self.pubsub_broadcast(
                func, success_topic_suffix, *kwarg_names
            )
        else:
            wrapped_func = self.pubsub_errors(func)

        topic_name = f"{self.topic}.{topic_name_suffix}"
        self._subscriptions.append((wrapped_func, topic_name))
        pub.subscribe(wrapped_func, topic_name)
