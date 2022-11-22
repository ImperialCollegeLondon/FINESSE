"""Code for FINESSE's main GUI window."""
from PySide6.QtWidgets import QMainWindow

from .serial_view import SerialPortControl


class MainWindow(QMainWindow):
    """The main window for FINESSE."""

    def __init__(self) -> None:
        """Create a new MainWindow."""
        super().__init__()
        self.setWindowTitle("FINESSE")

        devices = {
            "ST10": {"port": "COM5", "baud_rate": "9600"},
            "DP9800": {"port": "COM1", "baud_rate": "9600"},
        }
        serial_port = SerialPortControl(
            devices,
            ("COM1", "COM5", "COM7"),
            ("600", "9600", "115200"),
        )
        self.setCentralWidget(serial_port)
