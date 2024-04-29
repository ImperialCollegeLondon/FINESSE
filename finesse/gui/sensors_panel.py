"""Panel and widgets related to monitoring the interferometer."""

from collections.abc import Sequence

from pubsub import pub
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finesse.config import SENSORS_TOPIC
from finesse.gui.device_panel import DevicePanel
from finesse.gui.led_icon import LEDIcon
from finesse.sensor_reading import SensorReading


class SensorsPanel(DevicePanel):
    """Panel containing widgets to view sensor readings."""

    def __init__(self) -> None:
        """Create a new SensorsPanel."""
        super().__init__(SENSORS_TOPIC, "Sensor readings")

        self._val_lineedits: dict[str, QLineEdit] = {}

        self._poll_light = LEDIcon.create_green_icon()

        self._create_layouts()

        self._poll_wid_layout.addWidget(QLabel("POLL Server"))
        self._poll_wid_layout.addWidget(self._poll_light)
        self._poll_light.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self.setLayout(self._layout)

        # Listen for readings sent by backend
        pub.subscribe(self._on_readings_received, f"device.{SENSORS_TOPIC}.data")

    def _create_layouts(self) -> None:
        """Creates layouts to house the widgets."""
        self._poll_wid_layout = QHBoxLayout()
        self._reading_wid_layout = QFormLayout()

        top = QWidget()
        top.setLayout(self._reading_wid_layout)
        bottom = QWidget()
        bottom.setLayout(self._poll_wid_layout)

        self._layout = QVBoxLayout()
        self._layout.addWidget(top)
        self._layout.addWidget(bottom)

    def _get_reading_lineedit(self, reading: SensorReading) -> QLineEdit:
        """Get or create the QLineEdit for a given sensor.

        Args:
            reading: The sensor reading to display

        Returns:
            QLineEdit: the QLineEdit widget corresponding to the reading
        """
        if reading.name not in self._val_lineedits:
            label = QLabel(reading.name)
            label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            val_lineedit = QLineEdit()
            val_lineedit.setReadOnly(True)
            val_lineedit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lineedit.setSizePolicy(
                QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed
            )

            self._val_lineedits[reading.name] = val_lineedit
            self._reading_wid_layout.addRow(reading.name, val_lineedit)

        return self._val_lineedits[reading.name]

    def _on_readings_received(self, readings: Sequence[SensorReading]):
        """Receive sensor readings from the backend and update the GUI.

        Args:
            readings: the latest sensor readings received
        """
        self._poll_light.flash()
        for reading in readings:
            lineedit = self._get_reading_lineedit(reading)
            lineedit.setText(reading.val_str())
