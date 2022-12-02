"""Code for FINESSE's main GUI window."""
from PySide6.QtWidgets import QGridLayout, QGroupBox, QMainWindow, QWidget

from .opus_view import OPUSControl
from .serial_view import SerialPortControl
from .temp_control import DP9800, TC4820, BBMonitor


class MainWindow(QMainWindow):
    """The main window for FINESSE."""

    def __init__(self) -> None:
        """Create a new MainWindow."""
        super().__init__()
        self.setWindowTitle("FINESSE")

        layout = QGridLayout()

        devices = {
            "ST10": {"port": "COM5", "baud_rate": "9600"},
            "DP9800": {"port": "COM1", "baud_rate": "9600"},
        }
        serial_port: QGroupBox = SerialPortControl(
            devices,
            ("COM1", "COM5", "COM7"),
            ("600", "9600", "115200"),
        )
        opus: QGroupBox = OPUSControl("127.0.0.1")

        bb_monitor: QGroupBox = BBMonitor()
        dp9800: QGroupBox = DP9800()
        tc4820_hot: QGroupBox = TC4820("HOT")
        tc4820_cold: QGroupBox = TC4820("COLD")

        layout.addWidget(serial_port, 3, 0)
        layout.addWidget(opus, 0, 1)
        layout.addWidget(bb_monitor, 1, 1, 1, 2)
        layout.addWidget(dp9800, 2, 1, 1, 2)
        layout.addWidget(tc4820_hot, 3, 1, 1, 1)
        layout.addWidget(tc4820_cold, 3, 2, 1, 1)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)
