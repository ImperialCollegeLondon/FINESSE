"""Provides a control for viewing and connecting to devices."""
from typing import cast

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

from finesse.device_info import DeviceBaseTypeInfo, DeviceTypeInfo


def _create_device_widgets(types: list[DeviceTypeInfo]) -> list[QWidget | None]:
    """Create widgets for the specified device types."""
    widgets: list[QWidget | None] = []
    device_params = (t.parameters for t in types)
    for params in device_params:
        # Don't bother making a widget if there are no parameters
        if not params:
            widgets.append(None)
            continue

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
            if param.default_value is not None:
                combo.setCurrentText(param.default_value)

            layout.addWidget(combo)

    return widgets


class DeviceTypeControl(QGroupBox):
    """A set of widgets for choosing a device and its params and connecting to it."""

    def __init__(self, description: str, types: list[DeviceTypeInfo]) -> None:
        """Create a new DeviceTypeControl.

        Args:
            description: A description of the device type
            types: The available devices for this device type.
        """
        if not types:
            raise RuntimeError("At least one device type must be specified")

        super().__init__(description)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._devices = [t.description for t in types]
        """The names of the devices."""

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._device_combo = QComboBox()
        """Combo box allowing the user to choose the device."""
        self._device_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._device_combo.addItems(self._devices)
        self._device_combo.currentIndexChanged.connect(self._on_device_selected)
        layout.addWidget(self._device_combo)

        self._device_widgets: list[QWidget | None] = _create_device_widgets(types)
        """Widgets containing combo boxes specific to each parameter."""

        if self._device_widgets and (current := self._device_widgets[0]):
            # Show the combo boxes for the device's parameters
            current.show()
            layout.addWidget(current)

        # TODO: Button should be disabled if there are no options for one of the
        # params (e.g. there are no USB serial devices available)
        self._open_close_btn = QPushButton("Open")
        self._open_close_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._open_close_btn.setCheckable(True)
        layout.addWidget(self._open_close_btn)

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


class DeviceControl(QGroupBox):
    """Allows for viewing and connecting to devices."""

    def __init__(self) -> None:
        """Create a new DeviceControl."""
        super().__init__("Device control")
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.setLayout(QVBoxLayout())
        pub.subscribe(self._on_device_list, "serial.list")

    def _on_device_list(
        self, device_types: dict[DeviceBaseTypeInfo, list[DeviceTypeInfo]]
    ) -> None:
        layout = cast(QVBoxLayout, self.layout())

        # Group together devices based on their base types (e.g. "stepper motor")
        for base_type, types in device_types.items():
            if not base_type.names_long:
                layout.addWidget(DeviceTypeControl(base_type.description, types))
            else:
                for name in base_type.names_long:
                    layout.addWidget(
                        DeviceTypeControl(f"{base_type.description} ({name})", types)
                    )
