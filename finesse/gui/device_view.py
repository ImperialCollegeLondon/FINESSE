"""Provides a control for viewing and connecting to devices."""
from typing import cast

from pubsub import pub
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finesse.device_info import DeviceBaseTypeInfo, DeviceInstanceRef, DeviceTypeInfo
from finesse.settings import settings


def _create_device_widgets(
    instance: DeviceInstanceRef, device_types: list[DeviceTypeInfo]
) -> list[QWidget | None]:
    """Create widgets for the specified device types."""
    widgets: list[QWidget | None] = []
    for t in device_types:
        params = t.parameters

        # Don't bother making a widget if there are no parameters
        if not params:
            widgets.append(None)
            continue

        # Previous parameter values are saved if a device opens successfully
        previous_param_values: dict[str, str] | None = settings.value(
            f"device/{instance.topic}/{t.description}/params"
        )

        widget = QWidget()
        widget.hide()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        widgets.append(widget)

        # Make a combo box for each parameter
        for param in params:
            combo = QComboBox()
            combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            combo.addItems(param.possible_values)

            if (
                previous_param_values
                and previous_param_values[param.name] in param.possible_values
            ):
                combo.setCurrentText(previous_param_values[param.name])
            elif param.default_value is not None:
                combo.setCurrentText(param.default_value)

            layout.addWidget(combo)

    return widgets


class DeviceTypeControl(QGroupBox):
    """A set of widgets for choosing a device and its params and connecting to it."""

    def __init__(
        self,
        description: str,
        instance: DeviceInstanceRef,
        device_types: list[DeviceTypeInfo],
    ) -> None:
        """Create a new DeviceTypeControl.

        Args:
            description: A description of the device type
            instance: The device instance this panel is for
            device_types: The available devices for this base device type
        """
        if not device_types:
            raise RuntimeError("At least one device type must be specified")

        self._cur_device_params: dict[str, str]
        """Cache the device params used for opening the device."""
        self._device_instance = instance

        super().__init__(description)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._device_types = device_types
        """Type information for each of the device types for this base type."""

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._device_combo = QComboBox()
        """Combo box allowing the user to choose the device."""
        self._device_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        descriptions = [t.description for t in device_types]
        self._device_combo.addItems(descriptions)

        # Select the last device that was successfully opened, if there is one
        topic = instance.topic
        previous_device: str | None = settings.value(f"device/{instance.topic}/type")
        if previous_device and previous_device in descriptions:
            self._device_combo.setCurrentText(previous_device)

        self._device_combo.currentIndexChanged.connect(self._on_device_selected)
        layout.addWidget(self._device_combo)

        self._device_widgets: list[QWidget | None] = _create_device_widgets(
            instance, device_types
        )
        """Widgets containing combo boxes specific to each parameter."""

        if self._device_widgets and (
            current := self._device_widgets[self._get_device_idx()]
        ):
            # Show the combo boxes for the device's parameters
            current.show()
            layout.addWidget(current)

        # TODO: Button should be disabled if there are no options for one of the
        # params (e.g. there are no USB serial devices available)
        self._open_close_btn = QPushButton("Open")
        self._open_close_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._open_close_btn.clicked.connect(self._on_open_close_clicked)
        layout.addWidget(self._open_close_btn)

        # pubsub subscriptions
        pub.subscribe(self._on_device_opened, f"device.opened.{topic}")
        pub.subscribe(self._on_device_closed, f"device.closed.{topic}")
        pub.subscribe(self._show_error_message, f"device.error.{topic}")

    def _on_device_selected(self, device_idx: int) -> None:
        """Swap out the parameter combo boxes for the current device.

        Args:
            device_idx: Which device has been selected.
        """
        layout = cast(QHBoxLayout, self.layout())

        # If there's already a widget in place, remove it
        if layout.count() == 3:
            # For some reason we also have to hide the widget else it appears over the
            # others
            layout.takeAt(1).widget().hide()

        # Add the widget for the newly selected parameter if needed
        if widget := self._device_widgets[device_idx]:
            widget.show()
            layout.insertWidget(1, widget)

    def _get_device_idx(self) -> int:
        """Get the index of the currently selected device type."""
        return self._device_combo.currentIndex()

    def _get_current_device_and_params(self) -> tuple[DeviceTypeInfo, dict[str, str]]:
        """Get the current device type and associated parameters."""
        device_idx = self._get_device_idx()
        device_type = self._device_types[device_idx]

        # The current device widget contains combo boxes with the values
        widget = self._device_widgets[device_idx]
        if not widget:
            # No parameters needed for this device type
            return device_type, {}

        # Get the parameter values
        combos: list[QComboBox] = widget.findChildren(QComboBox)
        device_params = {
            p.name: c.currentText() for p, c in zip(device_type.parameters, combos)
        }

        return device_type, device_params

    def _set_combos_enabled(self, enabled: bool) -> None:
        """Set the enabled state of the combo boxes."""
        self._device_combo.setEnabled(enabled)

        if widget := self._device_widgets[self._get_device_idx()]:
            widget.setEnabled(enabled)

    def _open_device(self) -> None:
        """Open the currently selected device."""
        device_type, self._cur_device_params = self._get_current_device_and_params()
        pub.sendMessage(
            "device.open",
            module=device_type.module,
            class_name=device_type.class_name,
            instance=self._device_instance,
            params=self._cur_device_params,
        )

    def _on_device_opened(self) -> None:
        """Update the GUI for when the device is successfully opened."""
        settings.setValue(
            f"device/{self._device_instance.topic}/type",
            self._device_combo.currentText(),
        )
        if self._cur_device_params:
            settings.setValue(
                f"device/{self._device_instance.topic}/"
                f"{self._device_combo.currentText()}/params",
                self._cur_device_params,
            )

        self._set_combos_enabled(False)
        self._open_close_btn.setText("Close")

    def _close_device(self) -> None:
        """Close the device."""
        pub.sendMessage("device.close", instance=self._device_instance)

    def _on_device_closed(self) -> None:
        """Update the GUI for when the device is closed."""
        self._set_combos_enabled(True)
        self._open_close_btn.setText("Open")

    def _show_error_message(
        self, instance: DeviceInstanceRef, error: BaseException
    ) -> None:
        """Show an error message when something has gone wrong with the device.

        Todo:
            The name of the device isn't currently very human readable.
        """
        QMessageBox(
            QMessageBox.Icon.Critical,
            "A device error has occurred",
            "A fatal error has occurred with the "
            f"{instance.topic} device: {error!s}",
        ).exec()

    def _on_open_close_clicked(self) -> None:
        """Open/close the connection of the chosen device when the button is pushed."""
        if self._open_close_btn.text() == "Open":
            self._open_device()
        else:
            self._close_device()


class DeviceControl(QGroupBox):
    """Allows for viewing and connecting to devices."""

    def __init__(self) -> None:
        """Create a new DeviceControl."""
        super().__init__("Device control")
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setLayout(QVBoxLayout())

        # pubsub topics
        pub.subscribe(self._on_device_list, "device.list")

    def _on_device_list(
        self, device_types: dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]]
    ) -> None:
        layout = cast(QVBoxLayout, self.layout())

        # Group together devices based on their base types (e.g. "stepper motor")
        for base_type, types in device_types.items():
            if not base_type.names_long:
                layout.addWidget(
                    DeviceTypeControl(
                        base_type.description, DeviceInstanceRef(base_type.name), types
                    )
                )
            else:
                for short, long in zip(base_type.names_short, base_type.names_long):
                    layout.addWidget(
                        DeviceTypeControl(
                            f"{base_type.description} ({long})",
                            DeviceInstanceRef(base_type.name, short),
                            types,
                        )
                    )
