"""Code for FINESSE's main GUI window."""
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from ..config import APP_NAME
from .opus_view import OPUSControl
from .serial_view import SerialPortControl
from .stepper_motor_view import StepperMotorControl
from .temp_control import DP9800, TC4820, BBMonitor
from .uncaught_exceptions import set_uncaught_exception_handler


class MainWindow(QMainWindow):
    """The main window for FINESSE."""

    def __init__(self) -> None:
        """Create a new MainWindow."""
        super().__init__()
        self.setWindowTitle(APP_NAME)

        set_uncaught_exception_handler(self)

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
        )

        layout_left.addWidget(stepper_motor)
        layout_left.addWidget(serial_port)

        layout_right = QGridLayout()
        opus: QGroupBox = OPUSControl()
        layout_right.addWidget(opus, 0, 0, 1, 2)

        bb_monitor: QGroupBox = BBMonitor()
        dp9800: QGroupBox = DP9800(8)
        tc4820_hot: QGroupBox = TC4820("hot")
        tc4820_cold: QGroupBox = TC4820("cold")

        layout_right.addWidget(bb_monitor, 1, 0, 1, 2)
        layout_right.addWidget(dp9800, 2, 0, 1, 2)
        layout_right.addWidget(tc4820_hot, 3, 0, 1, 1)
        layout_right.addWidget(tc4820_cold, 3, 1, 1, 1)

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
