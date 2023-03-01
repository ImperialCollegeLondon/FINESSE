"""Panel and widgets related to monitoring the interferometer."""
from dataclasses import dataclass
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QSizePolicy

from .led_icons import LEDIcon


@dataclass
class EM27Property:
    """Class for representing EM27 monitored properties.

    Args:
        name: name of the physical quantity
        value: value of the physical quantity
        unit: unit in which the value is presented
    """

    name: str
    value: Decimal
    unit: str


def get_vals_from_server() -> list[EM27Property]:
    """Placeholder function for retrieving interferometer properties.

    Returns:
        data_table: A list containing the physical properties being monitored
    """
    data_table = [
        EM27Property("PSF27 Temp", Decimal(28.151062), "deg. C"),
        EM27Property("Cryo Temp", Decimal(0.0), "deg. K"),
        EM27Property("Blackbody Hum", Decimal(2.463968), "%"),
        EM27Property("Source Temp", Decimal(70.007156), "deg. C"),
        EM27Property("Aux Volt", Decimal(6.285875), "V"),
        EM27Property("Aux Curr", Decimal(0.910230), "A"),
        EM27Property("Laser Curr", Decimal(0.583892), "A"),
    ]
    return data_table


class EM27Monitor(QGroupBox):
    """Panel containing widgets to view the EM27 properties."""

    def __init__(self) -> None:
        """Creates the attributes required to view properties monitored by the EM27."""
        super().__init__("EM27 SOH Monitor")

        self._layout = QGridLayout()
        self._prop_names: list[str] = []
        self._prop_labels: list[QLabel] = []
        self._val_lineedits: list[QLineEdit] = []
        self._data_table: list[EM27Property] = []
        self._num_props = 0
        self._poll_light = LEDIcon.create_poll_icon()
        self._poll_light._timer.timeout.connect(self.poll_server)  # type: ignore
        self._poll_light._timer.start(2000)
        self._layout.addWidget(QLabel("POLL Server"), 0, 0)
        self._layout.addWidget(self._poll_light, 0, 1)
        self._poll_light.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed  # type: ignore
        )
        self.setLayout(self._layout)

    def _display_props(self) -> None:
        """Creates and populates the widgets to view the EM27 properties."""
        for prop in self._data_table:
            if prop.name not in self._prop_names:
                # Update list of monitored properties and create corresponding label
                self._prop_names.append(prop.name)
                prop_label = QLabel(prop.name)
                self._prop_labels.append(prop_label)

                # Remove poll server label and icon before adding new property widgets
                poll_server_label = self._layout.itemAtPosition(
                    self._num_props, 0
                ).widget()
                self._layout.removeWidget(poll_server_label)
                self._layout.removeWidget(self._poll_light)

                self._layout.addWidget(prop_label, self._num_props, 0)

                val_lineedit = QLineEdit()
                val_lineedit.setText(f"{prop.value:.6f} {prop.unit}")
                val_lineedit.setReadOnly(True)
                val_lineedit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._val_lineedits.append(val_lineedit)
                self._layout.addWidget(val_lineedit, self._num_props, 1)

                # Add poll server label and icon to bottom
                self._layout.addWidget(poll_server_label, self._num_props + 1, 0)
                self._layout.addWidget(self._poll_light, self._num_props + 1, 1)

                self._num_props += 1
            else:
                idx = self._prop_names.index(prop.name)
                self._val_lineedits[idx].setText(f"{prop.value:.6f} {prop.unit}")

    def poll_server(self) -> None:
        """Polls the server to obtain the latest values."""
        self._poll_light._flash()
        self._data_table = get_vals_from_server()
        self._display_props()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    em27_monitor = EM27Monitor()

    window.setCentralWidget(em27_monitor)
    window.show()
    app.exec()
