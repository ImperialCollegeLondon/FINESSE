"""Panel and widgets related to monitoring the aircraft flight parameters."""

from pubsub import pub
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from finesse.config import DECADES_TOPIC
from finesse.gui.device_panel import DevicePanel
from finesse.gui.led_icon import LEDIcon


class DECADESMonitor(DevicePanel):
    """Panel containing widgets to view the DECADES parameters."""

    def __init__(self) -> None:
        """Creates the attributes required to view properties monitored by DECADES."""
        super().__init__(DECADES_TOPIC, "DECADES Monitor")

        self._val_lineedits: dict[str, QLineEdit] = {}

        self._poll_light = LEDIcon.create_green_icon()

        self._create_layouts()

        self._poll_wid_layout.addWidget(QLabel("POLL Server"))
        self._poll_wid_layout.addWidget(self._poll_light)
        self._poll_light.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self.setLayout(self._layout)

        # Listen for properties sent by DECADES backend
        pub.subscribe(
            self._on_properties_received, f"device.{DECADES_TOPIC}.data.response"
        )

    def _create_layouts(self) -> None:
        """Creates layouts to house the widgets."""
        self._poll_wid_layout = QHBoxLayout()
        self._prop_wid_layout = QGridLayout()

        top = QWidget()
        top.setLayout(self._prop_wid_layout)
        bottom = QWidget()
        bottom.setLayout(self._poll_wid_layout)

        self._layout = QVBoxLayout()
        self._layout.addWidget(top)
        self._layout.addWidget(bottom)

    def _get_prop_lineedit(self, prop: str) -> QLineEdit:
        """Create and populate the widgets for displaying a given parameter.

        Args:
            prop: the DECADES parameter to display

        Returns:
            QLineEdit: the QLineEdit widget corresponding to the property
        """
        if prop not in self._val_lineedits:
            prop_label = QLabel(prop)
            prop_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            val_lineedit = QLineEdit()
            val_lineedit.setReadOnly(True)
            val_lineedit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lineedit.setSizePolicy(
                QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed
            )

            self._val_lineedits[prop] = val_lineedit

            num_props = len(self._val_lineedits)
            self._prop_wid_layout.addWidget(prop_label, num_props, 0)
            self._prop_wid_layout.addWidget(val_lineedit, num_props, 1)

        return self._val_lineedits[prop]

    def _on_properties_received(self, data: dict[str, float]):
        """Receive the data table from the server and update the GUI.

        Args:
            data: the properties received from the server
        """
        self._poll_light.flash()
        for prop in data:
            lineedit = self._get_prop_lineedit(prop[0])
            lineedit.setText(f"{prop[1]:.6f} {prop[2]}")


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    decades_monitor = DECADESMonitor()

    window.setCentralWidget(decades_monitor)
    window.show()
    app.exec()
