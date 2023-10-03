"""Provides a control for viewing and connecting to devices."""
from typing import cast

from pubsub import pub
from PySide6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QLabel, QPushButton


class DeviceControl(QGroupBox):
    """Allows for viewing and connecting to devices."""

    def __init__(self) -> None:
        """Create a new DeviceControl."""
        super().__init__("Device control")
        self.setLayout(QGridLayout())
        pub.subscribe(self._on_device_list, "serial.list")

    def _on_device_list(self, device_types: dict[str, list[str]]) -> None:
        layout = cast(QGridLayout, self.layout())

        # Group together devices based on their base types (e.g. "stepper motor")
        for row, (description, types) in enumerate(device_types.items()):
            label = QLabel(description)
            combo = QComboBox()
            combo.addItems(types)
            btn = QPushButton("Open")
            layout.addWidget(label, row, 0)
            layout.addWidget(combo, row, 1)
            layout.addWidget(btn, row, 2)
