"""Panel and widgets related to the control of the serial ports."""
import logging
from dataclasses import dataclass
from typing import Sequence

from pubsub import pub
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
)
from serial.tools.list_ports import comports

from ..config import (
    ALLOW_DUMMY_DEVICES,
    BAUDRATES,
    DEFAULT_ST10_BAUDRATE,
    DEFAULT_TC4820_BAUDRATE,
    DUMMY_DEVICE_PORT,
    STEPPER_MOTOR_TOPIC,
    TEMPERATURE_CONTROLLER_TOPIC,
)


def get_usb_serial_ports() -> list[str]:
    """Get the ports for connected USB serial devices."""
    # Vendor ID is a USB-specific field, so we can use this to check whether the device
    # is USB or not
    return sorted(port.device for port in comports() if port.vid is not None)


def get_default_ports() -> list[str]:
    """Get the default serial ports."""
    ports = get_usb_serial_ports()
    if ALLOW_DUMMY_DEVICES:
        ports.append(DUMMY_DEVICE_PORT)
    return ports


@dataclass
class Device:
    """The parameters to use for a particular device."""

    label: str
    """A human-readable label for the device"""
    name: str
    """The name of the device as used in pubsub topic"""
    default_baudrate: int
    """The default baudrate to select for the device"""


class DeviceControls:
    """A set of controls for opening/closing a connection to a single serial device."""

    def __init__(
        self,
        layout: QGridLayout,
        row: int,
        device: Device,
        avail_ports: Sequence[str],
        avail_baudrates: Sequence[int],
    ) -> None:
        """Create a new DeviceControls.

        The controls are added as a new row to a QGridLayout.

        Args:
            layout: The QGridLayout to add the controls to
            row: The row of the QGridLayout to add the controls to
            device: The device these controls refer to
            avail_ports: Possible serial ports to choose from
            avail_baudrates: Possible baudrates to choose from
        """
        self.name = device.name
        self.label = device.label

        # Add a label showing the device name
        layout.addWidget(QLabel(self.label), row, 0)

        self.ports = QComboBox()
        """The available serial ports for the device."""
        self.ports.addItems(avail_ports)
        # TODO: Remember which port was used last time
        layout.addWidget(self.ports, row, 1)

        self.baudrates = QComboBox()
        """The available baudrates for the device."""
        self.baudrates.addItems([str(br) for br in avail_baudrates])
        # TODO: Remember which baudrate was used last time
        layout.addWidget(self.baudrates, row, 2)

        if device.default_baudrate not in avail_baudrates:
            raise ValueError("Invalid default baudrate supplied")
        self.baudrates.setCurrentText(str(device.default_baudrate))

        self.open_close_btn = QPushButton("Open")
        """A button for opening and closing the port manually."""
        self.open_close_btn.setCheckable(True)
        self.open_close_btn.clicked.connect(self._on_open_close_clicked)  # type: ignore
        layout.addWidget(self.open_close_btn, row, 3)
        self.open_close_btn.setChecked(False)

        pub.subscribe(self._set_button_to_close, f"serial.{self.name}.opened")
        pub.subscribe(self._set_button_to_open, f"serial.{self.name}.close")
        pub.subscribe(self._show_error_message, f"serial.{self.name}.error")

    def _set_button_to_open(self):
        """Change the button to say Open."""
        self.open_close_btn.setText("Open")
        self.open_close_btn.setChecked(False)

    def _set_button_to_close(self):
        """Change the button to say Close."""
        self.open_close_btn.setText("Close")
        self.open_close_btn.setChecked(True)

    def _show_error_message(self, error: BaseException) -> None:
        """Show an error message when something has gone wrong with the device."""
        QMessageBox(
            QMessageBox.Icon.Critical,
            "A device error has occurred",
            f"A fatal error has occurred with the {self.label} device.",
        ).exec()

    def _open_device(self) -> None:
        """Open the specified serial device."""
        logging.info(f"Opening device {self.name}...")

        port = self.ports.currentText()
        baudrate = int(self.baudrates.currentText())
        pub.sendMessage(f"serial.{self.name}.open", port=port, baudrate=baudrate)

    def _close_device(self) -> None:
        """Close the specified serial device."""
        pub.sendMessage(f"serial.{self.name}.close")
        logging.info(f"Port for device {self.name} is closed")

    def _on_open_close_clicked(self) -> None:
        """Open/close the connection of the chosen device when the button is pushed."""
        if self.open_close_btn.text() == "Open":
            self._open_device()
        else:
            self._close_device()


class SerialPortControl(QGroupBox):
    """Widgets to control the communication with serial ports."""

    def __init__(
        self,
        devices: Sequence[Device] = (
            Device("ST10", STEPPER_MOTOR_TOPIC, DEFAULT_ST10_BAUDRATE),
            Device(
                "TC4820 Hot",
                f"{TEMPERATURE_CONTROLLER_TOPIC}.hot_bb",
                DEFAULT_TC4820_BAUDRATE,
            ),
            Device(
                "TC4820 Cold",
                f"{TEMPERATURE_CONTROLLER_TOPIC}.cold_bb",
                DEFAULT_TC4820_BAUDRATE,
            ),
        ),
        avail_ports: Sequence[str] = get_default_ports(),
        avail_baudrates: Sequence[int] = BAUDRATES,
    ) -> None:
        """Creates a sequence of widgets to control a serial connection to a device.

        Args:
            devices: The names of devices to list (for pubsub messages)
            avail_ports: Sequence of available USB serial ports
            avail_baudrates: Sequence of possible baudrates
        """
        super().__init__("Serial port control")

        layout = QGridLayout()
        self._devices = [
            DeviceControls(layout, i, device, avail_ports, avail_baudrates)
            for i, device in enumerate(devices)
        ]

        self.setLayout(layout)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    serial_port = SerialPortControl()
    window.setCentralWidget(serial_port)
    window.show()
    app.exec()
