"""Provides a panel for choosing between hardware sets and (dis)connecting."""
from collections.abc import Mapping
from typing import Any, cast

from frozendict import frozendict
from pubsub import pub
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
)

from finesse.device_info import DeviceInstanceRef
from finesse.gui.hardware_set.hardware_set import (
    HardwareSet,
    OpenDeviceArgs,
    load_builtin_hardware_sets,
)
from finesse.settings import settings


class HardwareSetsControl(QGroupBox):
    """A panel for choosing between hardware sets and (dis)connecting."""

    def __init__(self) -> None:
        """Create a new HardwareSetsControl."""
        super().__init__("Hardware set")

        self._connected_devices: set[OpenDeviceArgs] = set()
        pub.subscribe(self._on_device_opened, "device.opening")
        pub.subscribe(self._on_device_closed, "device.closed")

        self._hardware_sets_combo = QComboBox()
        self._hardware_sets_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        # Populate combo box
        for hw_set in load_builtin_hardware_sets():
            self._add_hardware_set(hw_set)

        # Remember which hardware set was in use the last time the program was run
        last_selected = cast(str | None, settings.value("hardware_set/selected"))
        if last_selected:
            self._hardware_sets_combo.setCurrentText(last_selected)

        self._hardware_sets_combo.currentIndexChanged.connect(
            self._update_control_state
        )

        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self._connect_btn.pressed.connect(self._on_connect_btn_pressed)
        self._disconnect_btn = QPushButton("Disconnect all")
        self._disconnect_btn.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self._disconnect_btn.pressed.connect(self._on_disconnect_btn_pressed)

        # Enable/disable controls
        self._update_control_state()

        layout = QHBoxLayout()
        layout.addWidget(self._hardware_sets_combo)
        layout.addWidget(self._connect_btn)
        layout.addWidget(self._disconnect_btn)
        self.setLayout(layout)

    def _add_hardware_set(self, hw_set: HardwareSet) -> None:
        """Add a new hardware set to the combo box."""
        labels = {
            self._hardware_sets_combo.itemText(i)
            for i in range(self._hardware_sets_combo.count())
        }
        if hw_set.name not in labels:
            self._hardware_sets_combo.addItem(hw_set.name, hw_set)
            return

        # If there is already a hardware set by that name, append a number
        i = 2
        while True:
            name = f"{hw_set.name} ({i})"
            if name not in labels:
                self._hardware_sets_combo.addItem(name, hw_set)
                return
            i += 1

    @property
    def current_hardware_set(self) -> frozenset[OpenDeviceArgs]:
        """Return the currently selected hardware set."""
        return self._hardware_sets_combo.currentData().devices

    def _update_control_state(self) -> None:
        """Enable or disable the connect and disconnect buttons as appropriate."""
        # Enable the "Connect" button if there are any devices left to connect for this
        # hardware set
        all_connected = self._connected_devices.issuperset(self.current_hardware_set)
        self._connect_btn.setEnabled(not all_connected)

        # Enable the "Disconnect all" button if there are *any* devices connected at all
        self._disconnect_btn.setEnabled(bool(self._connected_devices))

    def _on_connect_btn_pressed(self) -> None:
        """Connect to all devices in current hardware set.

        If a device has already been opened with the same type and parameters, then we
        skip it. If a device of the same type but with different parameters has been
        opened, then it will be closed as we open the new device.
        """
        for device in self.current_hardware_set.difference(self._connected_devices):
            device.open()

        self._update_control_state()

    def _on_disconnect_btn_pressed(self) -> None:
        """Disconnect from all devices in current hardware set."""
        # We need to copy the set because its size will change as we close devices
        for device in self._connected_devices.copy():
            device.close()

        self._update_control_state()

    def _on_device_opened(
        self, instance: DeviceInstanceRef, class_name: str, params: Mapping[str, Any]
    ) -> None:
        """Add instance to _connected_devices and update GUI."""
        self._connected_devices.add(
            OpenDeviceArgs(instance, class_name, frozendict(params))
        )
        self._update_control_state()

    def _on_device_closed(self, instance: DeviceInstanceRef) -> None:
        """Remove instance from _connected devices and update GUI."""
        try:
            # Remove the device matching this instance type (there should be only one)
            self._connected_devices.remove(
                next(
                    device
                    for device in self._connected_devices
                    if device.instance == instance
                )
            )

            self._update_control_state()
        except StopIteration:
            # No device of this type found
            pass
