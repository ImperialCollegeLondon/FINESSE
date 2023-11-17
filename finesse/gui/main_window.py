"""Code for FINESSE's main GUI window."""

from pubsub import pub
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QMenu,
    QWidget,
)

from finesse.config import (
    APP_NAME,
    TEMPERATURE_MONITOR_COLD_BB_IDX,
    TEMPERATURE_MONITOR_HOT_BB_IDX,
)
from finesse.gui.data_file_view import DataFileControl
from finesse.gui.device_view import DeviceControl
from finesse.gui.docs_view import DocsViewer
from finesse.gui.em27_monitor import EM27Monitor
from finesse.gui.hardware_set.hardware_sets_view import HardwareSetsControl
from finesse.gui.measure_script.script_view import ScriptControl
from finesse.gui.opus_view import OPUSControl
from finesse.gui.stepper_motor_view import StepperMotorControl
from finesse.gui.temp_control import DP9800Controls, TC4820Controls, TemperaturePlot
from finesse.gui.uncaught_exceptions import set_uncaught_exception_handler


class MainWindow(QMainWindow):
    """The main window for FINESSE."""

    def __init__(self) -> None:
        """Create a new MainWindow."""
        super().__init__()
        self.setWindowTitle(APP_NAME)

        set_uncaught_exception_handler(self)

        docs_viewer = DocsViewer(self)
        helpmenu = QMenu("Help", self)
        helpmenu.addAction(docs_viewer)
        self.menuBar().addMenu(helpmenu)

        layout_left = QGridLayout()

        # For choosing hardware set
        hardware_sets = HardwareSetsControl()

        # Setup for stepper motor control
        stepper_motor = StepperMotorControl()

        # Setup for measure script panel
        measure_script = ScriptControl()

        # Setup for device panel
        device_control = DeviceControl()

        # Setup for interferometer monitor
        em27_monitor = EM27Monitor()

        opus: QGroupBox = OPUSControl()

        layout_left.addWidget(hardware_sets, 0, 0, 1, 2)
        layout_left.addWidget(stepper_motor, 1, 0, 1, 2)
        layout_left.addWidget(opus, 2, 0, 1, 2)
        layout_left.addWidget(measure_script, 3, 0, 1, 2)
        layout_left.addWidget(device_control, 4, 0, 1, 1)
        layout_left.addWidget(em27_monitor, 4, 1, 1, 1)

        layout_right = QGridLayout()

        bb_monitor: QGroupBox = TemperaturePlot()
        dp9800: QGroupBox = DP9800Controls()
        tc4820_hot: QGroupBox = TC4820Controls("hot", TEMPERATURE_MONITOR_HOT_BB_IDX)
        tc4820_cold: QGroupBox = TC4820Controls("cold", TEMPERATURE_MONITOR_COLD_BB_IDX)

        # Setup for data file widgets
        data_file = DataFileControl()

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
