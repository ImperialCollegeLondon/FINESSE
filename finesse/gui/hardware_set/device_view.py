"""Provides a control for viewing and connecting to devices."""
from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import AbstractSet, Any, cast

from pubsub import pub
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finesse.device_info import DeviceBaseTypeInfo, DeviceInstanceRef, DeviceTypeInfo
from finesse.gui.error_message import show_error_message
from finesse.gui.hardware_set.device_connection import close_device, open_device
from finesse.gui.hardware_set.hardware_set import OpenDeviceArgs
from finesse.settings import settings


class DeviceParametersWidget(QWidget):
    """A widget containing controls for setting a device's parameters."""

    def __init__(self, device_type: DeviceTypeInfo) -> None:
        """Create a new DeviceParametersWidget.

        Args:
            device_type: The device type whose parameters will be used
        """
        super().__init__()

        self.device_type = device_type
        """This value is not used within the class, but is stored for convenience."""

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Make a combo box for each parameter
        self._combos: dict[str, QComboBox] = {}
        for param in device_type.parameters:
            combo = QComboBox()
            combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            # Keep the "real" value along with its string representation, so that we can
            # pass it back to the backend on device open
            for value in param.possible_values:
                combo.addItem(str(value), value)

            if param.default_value is not None:
                combo.setCurrentIndex(param.possible_values.index(param.default_value))

            layout.addWidget(combo)
            self._combos[param.name] = combo

    def set_parameter_value(self, param: str, value: Any) -> None:
        """Set the relevant combo box's parameter value."""
        self._combos[param].setCurrentText(str(value))

    @property
    def current_parameter_values(self) -> dict[str, Any]:
        """Get all parameters and their current values."""
        return {param: combo.currentData() for param, combo in self._combos.items()}

    @classmethod
    def create_with_saved_param_values(
        cls, device_type: DeviceTypeInfo
    ) -> DeviceParametersWidget:
        """Create a DeviceParametersWidget using saved values for parameters."""
        widget = cls(device_type)
        widget.hide()  # will be shown when used

        # Previous parameter values are saved if a device opens successfully. Update the
        # combo boxes to these values.
        previous_param_values = cast(
            dict[str, Any] | None,
            settings.value(f"device/params/{device_type.class_name}"),
        )
        if previous_param_values:
            for param, value in previous_param_values.items():
                try:
                    widget.set_parameter_value(param, value)
                except Exception as error:
                    logging.warn(f"Error while setting param {param}: {error!s}")

        return widget


class DeviceTypeControl(QGroupBox):
    """A set of widgets for choosing a device and its params and connecting to it."""

    def __init__(
        self,
        description: str,
        instance: DeviceInstanceRef,
        device_types: Sequence[DeviceTypeInfo],
        connected_device_type: str | None,
    ) -> None:
        """Create a new DeviceTypeControl.

        Args:
            description: A description of the device type
            instance: The device instance this panel is for
            device_types: The available devices for this base device type
            connected_device_type: The class name for this device type, if opened
        """
        if not device_types:
            raise RuntimeError("At least one device type must be specified")

        self._device_instance = instance

        super().__init__(description)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._device_combo = QComboBox()
        """Combo box allowing the user to choose the device."""
        self._device_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Add names for devices to combo box along with relevant user data
        self._device_widgets: list[DeviceParametersWidget] = []
        for t in device_types:
            widget = DeviceParametersWidget.create_with_saved_param_values(t)
            self._device_combo.addItem(t.description, widget)

            # YUCK: We have to keep our own reference to widget, as self._device_combo
            # seemingly won't prevent it from being GC'd
            self._device_widgets.append(widget)

        # Select the last device that was successfully opened, if there is one
        topic = instance.topic
        previous_device = cast(
            str | None, settings.value(f"device/type/{instance.topic}")
        )
        if previous_device:
            self._select_device(previous_device)

        self._device_combo.currentIndexChanged.connect(self._on_device_selected)
        layout.addWidget(self._device_combo)

        # Show the combo boxes for the device's parameters
        current_widget = self.current_device_type_widget
        current_widget.show()
        layout.addWidget(current_widget)

        self._open_close_btn = QPushButton()
        self._open_close_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._open_close_btn.clicked.connect(self._on_open_close_clicked)
        layout.addWidget(self._open_close_btn)
        if connected_device_type:
            self._set_device_opened(connected_device_type)
        else:
            self._set_device_closed()

        # Determine whether the button should be enabled or not
        self._update_open_btn_enabled_state()

        # pubsub subscriptions
        pub.subscribe(self._on_device_opened, f"device.opening.{topic}")
        pub.subscribe(self._set_device_closed, f"device.closed.{topic}")
        pub.subscribe(self._show_error_message, f"device.error.{topic}")

    def _update_open_btn_enabled_state(self) -> None:
        """Enable button depending on whether there are options for all params.

        The "open" button should be disabled if there are no possible values for any
        of the params.
        """
        all_params = self.current_device_type_widget.device_type.parameters
        self._open_close_btn.setEnabled(all(p.possible_values for p in all_params))

    def _on_device_selected(self) -> None:
        """Swap out the parameter combo boxes for the current device."""
        layout = cast(QHBoxLayout, self.layout())

        # If there's already a widget in place, remove it
        if layout.count() == 3:
            # For some reason we also have to hide the widget else it appears over the
            # others
            layout.takeAt(1).widget().hide()

        # Add the widget for the newly selected parameter if needed
        widget = self.current_device_type_widget
        widget.show()
        layout.insertWidget(1, widget)

        # Enable/disable the "open" button
        self._update_open_btn_enabled_state()

    @property
    def current_device_type_widget(self) -> DeviceParametersWidget:
        """Get information about the currently selected device type."""
        return self._device_combo.currentData()

    @property
    def current_device_and_params(
        self,
    ) -> tuple[DeviceTypeInfo, dict[str, Any]]:
        """Get the current device type and associated parameters."""
        widget = self.current_device_type_widget
        return widget.device_type, widget.current_parameter_values

    def _set_combos_enabled(self, enabled: bool) -> None:
        """Set the enabled state of the combo boxes."""
        self._device_combo.setEnabled(enabled)
        self.current_device_type_widget.setEnabled(enabled)

    def _set_device_opened(self, class_name: str) -> None:
        """Update the GUI for when the device is opened."""
        self._set_combos_enabled(False)
        self._open_close_btn.setText("Close")
        self._select_device(class_name)

    def _select_device(self, class_name: str) -> None:
        """Select the device from the combo box which matches class_name.

        Todo: Select params too
        """
        try:
            idx = next(
                i
                for i in range(self._device_combo.count())
                if self._device_combo.itemData(i).device_type.class_name == class_name
            )
        except StopIteration:
            logging.warn(f"Unknown class_name for opened device: {class_name}")

        self._device_combo.setCurrentIndex(idx)

    def _set_device_closed(self, **kwargs) -> None:
        """Update the GUI for when the device is opened."""
        self._set_combos_enabled(True)
        self._open_close_btn.setText("Open")

    def _open_device(self) -> None:
        """Open the currently selected device."""
        device_type, device_params = self.current_device_and_params
        open_device(device_type.class_name, self._device_instance, device_params)

    def _on_device_opened(
        self, instance: DeviceInstanceRef, class_name: str, params: Mapping[str, Any]
    ) -> None:
        """Update the GUI on device open."""
        self._set_device_opened(class_name)

    def _close_device(self) -> None:
        """Close the device."""
        close_device(self._device_instance)

    def _show_error_message(
        self, instance: DeviceInstanceRef, error: BaseException
    ) -> None:
        """Show an error message when something has gone wrong with the device.

        Todo:
            The name of the device isn't currently very human readable.
        """
        show_error_message(
            self,
            f"A fatal error has occurred with the {instance.topic} device: {error!s}",
            title="Device error",
        )

    def _on_open_close_clicked(self) -> None:
        """Open/close the connection of the chosen device when the button is pushed."""
        if self._open_close_btn.text() == "Open":
            self._open_device()
        else:
            self._close_device()


class DeviceControl(QGroupBox):
    """Allows for viewing and connecting to devices."""

    def __init__(self, connected_devices: AbstractSet[OpenDeviceArgs]) -> None:
        """Create a new DeviceControl."""
        super().__init__("Device control")
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setLayout(QVBoxLayout())
        self._connected_devices = connected_devices
        """The devices already connected when the control is created."""

        # Retrieve the list of device plugins
        pub.subscribe(self._on_device_list, "device.list.response")
        pub.sendMessage("device.list.request")

    def _get_connected_device(self, instance: DeviceInstanceRef) -> str | None:
        """Get the class name of the connected device matching instance, if any."""
        try:
            return next(
                device.class_name
                for device in self._connected_devices
                if device.instance == instance
            )
        except StopIteration:
            return None

    def _on_device_list(
        self, device_types: Mapping[DeviceBaseTypeInfo, Sequence[DeviceTypeInfo]]
    ) -> None:
        """Populate with DeviceTypeControls when a list of devices is received."""
        layout = cast(QVBoxLayout, self.layout())

        # Group together devices based on their base types (e.g. "stepper motor")
        for base_type, types in device_types.items():
            for instance, description in base_type.get_instances_and_descriptions():
                layout.addWidget(
                    DeviceTypeControl(
                        description,
                        instance,
                        types,
                        self._get_connected_device(instance),
                    )
                )
