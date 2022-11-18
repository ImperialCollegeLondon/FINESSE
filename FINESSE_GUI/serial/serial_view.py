"""Panel and widgets related to the control of the serial ports."""
from functools import partial
from typing import Sequence

from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QPushButton, QWidget


class SerialPortControl(QWidget):
    """Widgets to control the communication with a single serial port."""

    def __init__(
        self,
        device_names: Sequence[str],
        ports: Sequence[str],
        baud_rates: Sequence[int],
        avail_ports: Sequence[str],
        avail_baud_rates: Sequence[int],
    ) -> None:
        super().__init__()

        layout = QGridLayout()

        for i, (name, port, baud_rate) in enumerate(
            zip(device_names, ports, baud_rates)
        ):
            layout.addWidget(QLabel(name), i, 0)

            _port = QComboBox()
            _port.addItems(list(avail_ports))
            _port.setCurrentText(port)
            _port.currentTextChanged.connect(
                partial(self.on_port_changed, device_name=name)
            )
            layout.addWidget(_port, i, 1)

            _brate = QComboBox()
            _brate.addItems([str(br) for br in avail_baud_rates])
            _brate.setCurrentText(str(baud_rate))
            layout.addWidget(_brate, i, 2)

            _open_close_btn = QPushButton("Open")
            layout.addWidget(_open_close_btn, i, 3)

        self.setLayout(layout)

    def on_port_changed(self, new_port: str, device_name: str) -> None:
        """Callback to deal with a change of port for the given device.

        Args:
            new_port: The new port selected.
            device_name: Name of the device affected.
        """
        print(device_name, new_port)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    serial_port = SerialPortControl(
        ["ST10", "DP9800"],
        ["COM5", "COM1"],
        [9600, 9600],
        ("COM1", "COM5", "COM7"),
        (600, 9600, 115200),
    )
    window.setCentralWidget(serial_port)
    window.show()
    app.exec()
