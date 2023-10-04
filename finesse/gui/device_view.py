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
)

from finesse.device_type import DeviceType


class DeviceTypeControl(QGroupBox):
    """A set of widgets for choosing a device and its params and connecting to it."""

    def __init__(self, description: str, types: list[DeviceType]) -> None:
        """Create a new DeviceTypeControl.

        Args:
            description: A description of the device type
            types: The available devices for this device type.
        """
        if not types:
            raise RuntimeError("At least one device type must be specified")

        super().__init__(description)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self._device_params = [t.params for t in types]
        """The parameters and their possible values for all devices."""

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._device_combo = QComboBox()
        """Combo box allowing the user to choose the device."""
        self._device_combo.addItems([t.description for t in types])
        self._device_combo.currentIndexChanged.connect(self._configure_combo_boxes)
        layout.addWidget(self._device_combo)

        self._param_combos: list[QComboBox] = []
        """Combo boxes for each param."""

        # We need enough combo boxes for the maximum possible number of params
        for _ in range(max(map(len, self._device_params))):
            combo = QComboBox()
            combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
            layout.addWidget(combo)
            self._param_combos.append(combo)

        # TODO: Button should be disabled if there are no options for one of the
        # params (e.g. there are no USB serial devices available)
        btn = QPushButton("Open")
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        layout.addWidget(btn)

        self._configure_combo_boxes(0)

    def _configure_combo_boxes(self, device_idx: int) -> None:
        """Update combo boxes for different parameter values.

        Args:
            device_idx: Which device has been selected.
        """
        # Update combo boxes with the possible values for this device and show
        params = self._device_params[device_idx]
        for i, param_values in enumerate(params.values()):
            combo = self._param_combos[i]
            combo.clear()
            combo.addItems(param_values)
            combo.setVisible(True)

        # Hide any leftover combo boxes
        for combo in self._param_combos[len(params) :]:
            combo.setVisible(False)


class DeviceControl(QGroupBox):
    """Allows for viewing and connecting to devices."""

    def __init__(self) -> None:
        """Create a new DeviceControl."""
        super().__init__("Device control")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        self.setLayout(QVBoxLayout())
        pub.subscribe(self._on_device_list, "serial.list")

    def _on_device_list(self, device_types: dict[str, list[DeviceType]]) -> None:
        layout = cast(QVBoxLayout, self.layout())

        # Group together devices based on their base types (e.g. "stepper motor")
        for description, types in device_types.items():
            layout.addWidget(DeviceTypeControl(description, types))
