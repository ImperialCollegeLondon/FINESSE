"""Code for FINESSE's main GUI window."""
from PySide6.QtWidgets import QGridLayout, QGroupBox, QMainWindow, QWidget


from .interferometer_monitor import EM27Monitor
from .opus_view import OPUSControl
from .serial_view import SerialPortControl


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

        layout.addWidget(serial_port, 3, 0)
        layout.addWidget(opus, 0, 1)

        # Setup for interferometer monitor
        prop_labels = [
            "PSF27 Temp",
            "Cryo Temp",
            "Blackbody Hum",
            "Source Temp",
            "AUX Volt",
            "AUX Current",
            "Laser Current",
            "POLL Server",
        ]
        prop_units = ["deg C", "K", "%", "deg C", "V", "A", "A", None]
        em27_monitor = EM27Monitor(prop_labels, prop_units)

        layout.addWidget(em27_monitor, 1, 1)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)
