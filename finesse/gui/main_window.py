"""Code for FINESSE's main GUI window."""
from pubsub import pub
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QMainWindow, QWidget

from ..config import (
    APP_NAME,
    TEMPERATURE_MONITOR_COLD_BB_IDX,
    TEMPERATURE_MONITOR_HOT_BB_IDX,
)
from .data_file_view import DataFileControl
from .interferometer_monitor import EM27Monitor
from .measure_script.script_view import ScriptControl
from .opus_view import OPUSControl
from .serial_view import SerialPortControl
from .stepper_motor_view import StepperMotorControl
from .temp_control import DP9800Controls, TC4820Controls, TemperaturePlot
from .uncaught_exceptions import set_uncaught_exception_handler


class MainWindow(QMainWindow):
    """The main window for FINESSE."""

    def __init__(self) -> None:
        """Create a new MainWindow."""
        super().__init__()
        self.setWindowTitle(APP_NAME)

        set_uncaught_exception_handler(self)

        layout_left = QGridLayout()

        # Setup for stepper motor control
        stepper_motor = StepperMotorControl()

        # Setup for measure script panel
        measure_script = ScriptControl()

        # Setup for serial port control
        serial_port: QGroupBox = SerialPortControl()

        # Setup for interferometer monitor
        em27_monitor = EM27Monitor()

        # Setup for data file widgets
        data_file = DataFileControl()

        layout_left.addWidget(stepper_motor, 0, 0, 1, 2)
        layout_left.addWidget(measure_script, 1, 0, 1, 1)
        layout_left.addWidget(serial_port, 2, 0, 1, 1)
        layout_left.addWidget(em27_monitor, 2, 1, 1, 1)

        layout_right = QGridLayout()
        opus: QGroupBox = OPUSControl()
        layout_right.addWidget(opus, 0, 0, 1, 2)

        bb_monitor: QGroupBox = TemperaturePlot()
        dp9800: QGroupBox = DP9800Controls()
        tc4820_hot: QGroupBox = TC4820Controls("hot", TEMPERATURE_MONITOR_HOT_BB_IDX)
        tc4820_cold: QGroupBox = TC4820Controls("cold", TEMPERATURE_MONITOR_COLD_BB_IDX)

        layout_right.addWidget(bb_monitor, 1, 0, 1, 2)
        layout_right.addWidget(dp9800, 2, 0, 1, 2)
        layout_right.addWidget(tc4820_hot, 3, 0, 1, 1)
        layout_right.addWidget(tc4820_cold, 3, 1, 1, 1)
        layout_right.addWidget(data_file, 4, 0, 1, 2)

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

    def showEvent(self, event: QShowEvent) -> None:
        """Send window.opened message."""
        pub.sendMessage("window.opened")

    def hideEvent(self, event: QHideEvent) -> None:
        """Send window.closed message."""
        pub.sendMessage("window.closed")
