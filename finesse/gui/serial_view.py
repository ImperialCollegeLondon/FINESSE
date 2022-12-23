"""Panel and widgets related to the control of the serial ports."""
import logging
from copy import deepcopy
from functools import partial
from typing import Dict, Sequence

from PySide6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QLabel, QPushButton

from ..config import BAUDRATES


class SerialPortControl(QGroupBox):
    """Widgets to control the communication with serial ports."""

    def __init__(
        self,
        devices: Dict[str, Dict[str, str]],
        avail_ports: Sequence[str],
        avail_baud_rates: Sequence[int] = BAUDRATES,
    ) -> None:
        """Creates a sequence of widgets to control a serial connection to a device.

        Args:
            devices (Dict[str, Dict[str, str]]): Dictionary has a keys the names of the
                devices to control and as values a dictionary with the port and baud
                rate chosen for that device.
            avail_ports: Sequence of possible serial ports.
            avail_baud_rates: Sequence of possible baud rates.
        """
        super().__init__("Serial port control")

        self._devices = deepcopy(devices)
        self._is_open = {d: False for d in devices.keys()}
        layout = self._create_controls(avail_ports, avail_baud_rates)
        self.setLayout(layout)

    def _create_controls(
        self, avail_ports: Sequence[str], avail_baud_rates: Sequence[int]
    ) -> QGridLayout:
        """Creates the controls for the ports of the devices.

        Args:
            avail_ports: Sequence of possible serial ports.
            avail_baud_rates: Sequence of possible baud rates.

        Returns:
            QGridLayout: The layout with the widgets.
        """
        layout = QGridLayout()
        for i, (name, details) in enumerate(self._devices.items()):
            # Adding the device name
            layout.addWidget(QLabel(name), i, 0)

            # Its port
            _port = QComboBox()
            _port.addItems(list(avail_ports))
            _port.setCurrentText(details["port"])
            _port.currentTextChanged.connect(  # type: ignore
                partial(self.on_port_changed, device_name=name)
            )
            layout.addWidget(_port, i, 1)

            # Its baud rate
            _brate = QComboBox()
            _brate.addItems([str(br) for br in avail_baud_rates])
            _brate.setCurrentText(details["baud_rate"])
            _brate.currentTextChanged.connect(  # type: ignore
                partial(self.on_baud_rate_changed, device_name=name)
            )
            layout.addWidget(_brate, i, 2)

            # And a manual way to open/close it
            _open_close_btn = QPushButton("Open")
            _open_close_btn.setCheckable(True)
            _open_close_btn.released.connect(  # type: ignore
                partial(
                    self.on_open_close_clicked, device_name=name, button=_open_close_btn
                )
            )
            _open_close_btn.setChecked(False)
            layout.addWidget(_open_close_btn, i, 3)

        return layout

    def on_port_changed(self, new_port: str, device_name: str) -> None:
        """Callback to deal with a change of port for the given device.

        Args:
            new_port: The new port selected.
            device_name: Name of the device affected.
        """
        logging.info(
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
        logging.info(
            f"{device_name} - old baud_rate: {self._devices[device_name]['baud_rate']} "
            f"- new baud_rate: {new_baud_rate}"
        )
        self._devices[device_name]["port"] = new_baud_rate

    def on_open_close_clicked(self, device_name: str, button: QPushButton) -> None:
        """Open/Close the connection of the chosen device when the button is pushed.

        This method tries to open/close the device and, if successful, change the label
        on the button. Otherwise, it reverts back to the previous state.

        TODO: Do we need this? Not doing anything for now, obviously.

        Args:
            device_name: Name of the device affected.
            button: The button that sent the signal.
        """
        is_open = button.isChecked()
        try:
            # Try to open/close things
            pass
        except Exception:
            # and if they dont work...
            is_open = not is_open

        self._is_open[device_name] = is_open
        button.setChecked(is_open)
        button.setText("Close" if is_open else "Open")

        logging.info(f"Port for device {device_name} is open: {is_open}")


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
    )
    window.setCentralWidget(serial_port)
    window.show()
    app.exec()
