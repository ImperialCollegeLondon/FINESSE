"""Panel and widgets related to the control of the serial ports."""
from copy import deepcopy
from functools import partial
from typing import Dict, Sequence

from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QPushButton, QWidget


class SerialPortControl(QWidget):
    """Widgets to control the communication with a single serial port."""

    def __init__(
        self,
        devices: Dict[str, Dict[str, str]],
        avail_ports: Sequence[str],
        avail_baud_rates: Sequence[int],
    ) -> None:
        super().__init__()

        layout = QGridLayout()
        for i, (name, details) in enumerate(devices.items()):
            layout.addWidget(QLabel(name), i, 0)

            _port = QComboBox()
            _port.addItems(list(avail_ports))
            _port.setCurrentText(details["port"])
            _port.currentTextChanged.connect(
                partial(self.on_port_changed, device_name=name)
            )
            layout.addWidget(_port, i, 1)

            _brate = QComboBox()
            _brate.addItems([str(br) for br in avail_baud_rates])
            _brate.setCurrentText(details["baud_rate"])
            _brate.currentTextChanged.connect(
                partial(self.on_baud_rate_changed, device_name=name)
            )
            layout.addWidget(_brate, i, 2)

            _open_close_btn = QPushButton("Open")
            layout.addWidget(_open_close_btn, i, 3)

        self.setLayout(layout)
        self._devices = deepcopy(devices)

    def on_port_changed(self, new_port: str, device_name: str) -> None:
        """Callback to deal with a change of port for the given device.

        Args:
            new_port: The new port selected.
            device_name: Name of the device affected.
        """
        print(
            f"{device_name} - old port: {self._devices[device_name]['port']} "
            f"- new port: {new_port}"
        )
        self._devices[device_name]["port"] = new_port

    def on_baud_rate_changed(self, new_baud_rate: str, device_name: str) -> None:
        """Callback to deal with a change of baud rate for the given device.

        Args:
            new_baud_rate: The new port selected.
            device_name: Name of the device affected.
        """
        print(
            f"{device_name} - old baud_rate: {self._devices[device_name]['baud_rate']} "
            f"- new baud_rate: {new_baud_rate}"
        )
        self._devices[device_name]["port"] = new_baud_rate


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    devices = {
        "ST10": {"port": "COM5", "baud_rate": "9600"},
        "DP9800": {"port": "COM1", "baud_rate": "9600"},
    }
    serial_port = SerialPortControl(
        devices,
        ("COM1", "COM5", "COM7"),
        (600, 9600, 115200),
    )
    window.setCentralWidget(serial_port)
    window.show()
    app.exec()
