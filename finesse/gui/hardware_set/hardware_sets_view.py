"""Provides a panel for choosing between hardware sets and (dis)connecting."""
from collections.abc import Mapping
from pathlib import Path
from typing import AbstractSet, Any, cast

from frozendict import frozendict
from pubsub import pub
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finesse.device_info import DeviceInstanceRef
from finesse.gui.error_message import show_error_message
from finesse.gui.hardware_set.device_view import DeviceControl
from finesse.gui.hardware_set.hardware_set import (
    HardwareSet,
    OpenDeviceArgs,
    get_hardware_sets,
)
from finesse.settings import settings


class ManageDevicesDialog(QDialog):
    """A dialog for manually opening, closing and configuring devices."""

    def __init__(
        self, parent: QWidget, connected_devices: AbstractSet[OpenDeviceArgs]
    ) -> None:
        """Create a new ManageDevicesDialog.

        Args:
            parent: Parent window
            connected_devices: Which devices are already connected
        """
        super().__init__(parent)
        self.setWindowTitle("Manage devices")
        self.setModal(True)

        layout = QVBoxLayout()
        layout.addWidget(DeviceControl(connected_devices))
        self.setLayout(layout)


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
        self._load_hardware_set_list()
        self._load_last_selected_hardware_set()

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

        import_hw_set_btn = QPushButton("Import config")
        import_hw_set_btn.pressed.connect(self._import_hardware_set)

        self._remove_hw_set_btn = QPushButton("Remove")
        self._remove_hw_set_btn.pressed.connect(self._remove_current_hardware_set)

        manage_devices_btn = QPushButton("Manage devices")
        manage_devices_btn.pressed.connect(self._show_manage_devices_dialog)
        self._manage_devices_dialog: ManageDevicesDialog

        row1 = QHBoxLayout()
        row1.addWidget(self._hardware_sets_combo)
        row1.addWidget(self._connect_btn)
        row1.addWidget(self._disconnect_btn)
        row2 = QHBoxLayout()
        row2.addWidget(import_hw_set_btn)
        row2.addWidget(self._remove_hw_set_btn)
        row2.addWidget(manage_devices_btn)

        layout = QVBoxLayout()
        layout.addLayout(row1)
        layout.addLayout(row2)
        self.setLayout(layout)

        pub.subscribe(self._load_hardware_set_list, "hardware_set.removed")
        pub.subscribe(self._on_hardware_set_added, "hardware_set.added")

        self._update_control_state()

        self._hardware_sets_combo.currentIndexChanged.connect(
            self._update_control_state
        )

    def _load_last_selected_hardware_set(self) -> None:
        """Select the hardware set last selected when the program was run before."""
        if last_selected := cast(str | None, settings.value("hardware_set/selected")):
            self._hardware_sets_combo.setCurrentText(last_selected)

    def _load_hardware_set_list(self) -> None:
        """Populate the combo box with hardware sets."""
        self._hardware_sets_combo.clear()
        for hw_set in get_hardware_sets():
            self._add_hardware_set(hw_set)

    def _import_hardware_set(self) -> None:
        """Import a hardware set from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import hardware set config file", filter="*.yaml"
        )
        if not file_path:
            return

        try:
            hw_set = HardwareSet.load(Path(file_path))
        except Exception:
            show_error_message(
                self,
                "Could not load hardware set config file. Is it in the correct format?",
                "Could not load config file",
            )
        else:
            pub.sendMessage("hardware_set.add", hw_set=hw_set)

    def _remove_current_hardware_set(self) -> None:
        """Remove the currently selected hardware set."""
        pub.sendMessage(
            "hardware_set.remove", hw_set=self._hardware_sets_combo.currentData()
        )

    def _show_manage_devices_dialog(self) -> None:
        """Show a dialog for managing devices manually.

        The dialog is created lazily.
        """
        if not hasattr(self, "_manage_devices_dialog"):
            self._manage_devices_dialog = ManageDevicesDialog(
                self.window(), self._connected_devices
            )

        self._manage_devices_dialog.show()

    def _add_hardware_set(self, hw_set: HardwareSet) -> None:
        """Add a new hardware set to the combo box."""
        labels = {
            self._hardware_sets_combo.itemText(i)
            for i in range(self._hardware_sets_combo.count())
        }

        name_root = hw_set.name
        if hw_set.built_in:
            name_root += " (built in)"

        if name_root not in labels:
            self._hardware_sets_combo.addItem(name_root, hw_set)
            return

        # If there is already a hardware set by that name, append a number
        i = 2
        while True:
            name = f"{name_root} ({i})"
            if name not in labels:
                self._hardware_sets_combo.addItem(name, hw_set)
                return
            i += 1

    def _on_hardware_set_added(self, hw_set: HardwareSet) -> None:
        """Clear the combo box and refill it, then select hw_set.

        The reason for clearing the combo box and refilling it is so that we can keep
        the entries sorted.
        """
        self._load_hardware_set_list()

        # Select the just-added hardware set
        idx = next(
            i
            for i in range(self._hardware_sets_combo.count())
            if self._hardware_sets_combo.itemData(i) is hw_set
        )
        self._hardware_sets_combo.setCurrentIndex(idx)

    @property
    def current_hardware_set(self) -> frozenset[OpenDeviceArgs]:
        """Return the currently selected hardware set.

        If the combo box is empty and, therefore, no hardware set is selected, an empty
        set is returned.
        """
        hw_set = cast(HardwareSet | None, self._hardware_sets_combo.currentData())
        return hw_set.devices if hw_set else frozenset()

    def _update_control_state(self) -> None:
        """Enable or disable the connect and disconnect buttons as appropriate."""
        # Enable the "Connect" button if there are any devices left to connect for this
        # hardware set
        all_connected = self._connected_devices.issuperset(self.current_hardware_set)
        self._connect_btn.setEnabled(not all_connected)

        # Enable the "Disconnect all" button if there are *any* devices connected at all
        self._disconnect_btn.setEnabled(bool(self._connected_devices))

        # Enable the "Remove" button only if the hardware set is not a built in one
        hw_set = cast(HardwareSet | None, self._hardware_sets_combo.currentData())
        self._remove_hw_set_btn.setEnabled(hw_set is not None and not hw_set.built_in)

    def _on_connect_btn_pressed(self) -> None:
        """Connect to all devices in current hardware set.

        If a device has already been opened with the same type and parameters, then we
        skip it. If a device of the same type but with different parameters has been
        opened, then it will be closed as we open the new device.
        """
        # Remember which hardware set was selected for next time we run the program
        settings.setValue(
            "hardware_set/selected", self._hardware_sets_combo.currentText()
        )

        # Open each of the devices in turn
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

        # Remember last opened device
        settings.setValue(f"device/type/{instance!s}", class_name)
        if params:
            settings.setValue(f"device/params/{class_name}", params)

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
