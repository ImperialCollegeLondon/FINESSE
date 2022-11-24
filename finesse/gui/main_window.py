"""Code for FINESSE's main GUI window."""
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from ..config import APP_NAME
from .opus_view import OPUSControl
from .serial_view import SerialPortControl
from .stepper_motor_view import StepperMotorControl


class MainWindow(QMainWindow):
    """The main window for FINESSE."""

    def __init__(self) -> None:
        """Create a new MainWindow."""
        super().__init__()
        self.setWindowTitle(APP_NAME)

        layout_left = QVBoxLayout()

        # Setup for stepper motor control
        stepper_motor = StepperMotorControl()

        # Setup for serial port control
        devices = {
            "ST10": {"port": "COM5", "baud_rate": "9600"},
            "DP9800": {"port": "COM1", "baud_rate": "9600"},
        }
        serial_port: QGroupBox = SerialPortControl(
            devices,
            ("COM1", "COM5", "COM7"),
            ("600", "9600", "115200"),
        )

        layout_left.addWidget(stepper_motor)
        layout_left.addWidget(serial_port)

        layout_right = QVBoxLayout()
        opus: QGroupBox = OPUSControl("127.0.0.1")
        layout_right.addWidget(opus)

        # Display widgets in two columns
        left = QWidget()
        left.setLayout(layout_left)
        right = QWidget()
        right.setLayout(layout_right)
        layout = QHBoxLayout()
        layout.addWidget(left)
        layout.addWidget(right)
        central = QWidget()
        central.setLayout(layout)

        self.setCentralWidget(central)
