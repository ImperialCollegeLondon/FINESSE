"""Provides base classes for all types of devices.

The Device class is the top-level base class from which all devices ultimately inherit.
Concrete classes for devices must not inherit directly from this class, but instead
should inherit from a device base class.
"""

from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from inspect import isabstract, signature
from typing import Any, ClassVar, get_type_hints

from decorator import decorate
from pubsub import pub

from finesse.device_info import (
    DeviceBaseTypeInfo,
    DeviceInstanceRef,
    DeviceParameter,
    DeviceTypeInfo,
)
from finesse.hardware.plugins import __name__ as _plugins_name
from finesse.hardware.plugins import load_all_plugins

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

    _device_base_type_info: ClassVar[DeviceBaseTypeInfo]
    """Information about the device's base type."""
    _device_description: ClassVar[str]
    """A human-readable name."""
    _device_parameters: ClassVar[dict[str, DeviceParameter]] = {}
    """Possible parameters that this device type accepts.

    The key represents the parameter name and the value is a list of possible values.
    """

    def __init_subclass__(
        cls, parameters: Mapping[str, str | tuple[str, Sequence]] = {}
    ) -> None:
        """Initialise a device class.

        Args:
            parameters: Extra device parameters that this class requires
        """
        super().__init_subclass__()

        # Every time we create a new class, create a new _device_parameters attribute,
        # so that _add_parameters() and _update_parameter_defaults() don't clobber
        # values for the parent class.
        cls._device_parameters = deepcopy(cls._device_parameters)

        cls._add_parameters(parameters)
        cls._update_parameter_defaults()

    @classmethod
    def _add_parameters(
        cls,
        parameters: Mapping[str, str | tuple[str, Sequence]],
    ) -> None:
        """Store extra device parameters in a class attribute."""
        arg_types = get_type_hints(cls.__init__)
        for name, value in parameters.items():
            if isinstance(value, str):
                # Only a description provided
                try:
                    arg_type = arg_types[name]
                except KeyError:
                    raise ValueError(
                        f"The argument {name} was not found in "
                        f"{cls.__name__}'s constructor (or no type annotation given)."
                    )

                cls._device_parameters[name] = DeviceParameter(value, arg_type)
            elif isinstance(value, tuple):
                # A description and possible values provided
                cls._device_parameters[name] = DeviceParameter(value[0], value[1])
            else:
                # Bad type
                raise TypeError("Invalid parameters argument")

    @classmethod
    def _update_parameter_defaults(cls) -> None:
        """Add default values to device parameters from this class's constructor."""
        ctor_params = signature(cls).parameters
        for name, param in ctor_params.items():
            if name not in cls._device_parameters:
                continue

            default_value = param.default
            if default_value != param.empty:
                cls._device_parameters[name].default_value = default_value

    @abstractmethod
    def close(self) -> None:
        """Close the connection to the device."""

    @classmethod
    def get_device_parameters(cls) -> dict[str, DeviceParameter]:
        """Get the parameters for this device class."""
        return cls._device_parameters

    @classmethod
    def get_device_base_type_info(cls) -> DeviceBaseTypeInfo:
        """Get information about the base type for this device type."""
        return cls._device_base_type_info

    @classmethod
    def get_device_type_info(cls) -> DeviceTypeInfo:
        """Get information about this device type."""
        class_name_full = f"{cls.__module__}.{cls.__name__}"
        class_name = class_name_full.removeprefix(f"{_plugins_name}.")
        if len(class_name) == len(class_name_full):
            raise RuntimeError(f"Plugins must be in {_plugins_name}")

        return DeviceTypeInfo(
            class_name,
            cls._device_description,
            cls.get_device_parameters(),
        )


class Device(AbstractDevice):
    """A base class for device types.

    This class is the base class for device base types and (indirectly) concrete device
    type classes. Unlike AbstractDevice, it provides an __init_subclass__ method to
    initialise the its subclasses differently depending on whether or not they are
    defined as device base types or not.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialise a device type class."""
        if _base_types.isdisjoint(cls.__mro__):
            # If the class doesn't inherit from a base type it must be a base type
            # itself
            cls._init_base_type(**kwargs)
        elif not isabstract(cls):
            # All *concrete* device classes which inherit from a base type are treated
            # as device types. Abstract ones are ignored.
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
            f"device.error.{instance!s}",
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
                self.send_message(
                    success_topic_suffix, **dict(zip(kwarg_names, result))
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

    def send_message(self, topic_suffix: str, **kwargs: Any) -> None:
        """Send a pubsub message for this device.

        Args:
            topic_suffix: The part of the topic name after self.topic
            **kwargs: Extra arguments to include with pubsub message
        """
        pub.sendMessage(f"{self.topic}.{topic_suffix}", **kwargs)
