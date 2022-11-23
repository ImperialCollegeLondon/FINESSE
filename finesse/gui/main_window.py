"""Code for FINESSE's main GUI window."""
from PySide6.QtWidgets import QGridLayout, QMainWindow, QWidget

from .interferometer_monitor import EM27Monitor
from .serial_view import SerialPortControl
from .stepper_motor_view import StepperMotorControl


class MainWindow(QMainWindow):
    """The main window for FINESSE."""

    def __init__(self) -> None:
        """Create a new MainWindow."""
        super().__init__()
        self.setWindowTitle("FINESSE")

        # Setup for stepper motor control
        stepper_motor = StepperMotorControl()

        # Setup for serial port control
        devices = {
            "ST10": {"port": "COM5", "baud_rate": "9600"},
            "DP9800": {"port": "COM1", "baud_rate": "9600"},
        }
        serial_port = SerialPortControl(
            devices,
            ("COM1", "COM5", "COM7"),
            ("600", "9600", "115200"),
        )

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

        layout = QGridLayout()
        layout.addWidget(stepper_motor, 0, 0)
        layout.addWidget(serial_port, 1, 0)
        layout.addWidget(em27_monitor, 1, 1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
