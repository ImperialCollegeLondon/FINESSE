"""Panel and widgets related to monitoring the interferometer."""
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QSizePolicy

from .led_icons import LEDIcon


def get_vals_from_server() -> dict:
    """Placeholder function for retrieving interferometer properties.

    Returns:
        data_table: A dictionary containing the physical properties being monitored
    """
    data_table = {
        "PSF27 Temp": [28.151062, "deg. C"],
        "Cryo Temp": [0.0, "deg. K"],
        "Blackbody Hum": [2.463968, "%"],
        "Source Temp": [70.007156, "deg. C"],
        "Aux Volt": [6.285875, "V"],
        "Aux Curr": [0.910230, "A"],
        "Laser Curr": [0.583892, "A"],
    }
    return data_table


class EM27Monitor(QGroupBox):
    """Panel containing widgets to view the EM27 properties."""

    def __init__(self) -> None:
        """Creates the attributes required to view properties monitored by the EM27."""
        super().__init__("EM27 SOH Monitor")

        self._prop_labels: list[QLabel] = []
        self._val_lineedits: list[QLineEdit] = []
        self._data_table: Dict[str, list[Optional[str]]] = {}
        self._num_props = 0
        self._poll_light = LEDIcon.create_poll_icon()
        self._poll_light._timer.timeout.connect(self.poll_server)
        self._poll_light._timer.start(2000)

    #        self.poll_server()

    def _add_widgets(self) -> None:
        """Creates the widgets to view the EM27 properties."""
        layout = QGridLayout()

        for i, label in enumerate(self._data_table):
            prop_label = QLabel(label)
            self._prop_labels.append(prop_label)
            layout.addWidget(prop_label, i, 0)

            val_lineedit = QLineEdit()
            val_lineedit.setText(
                f"{self._data_table[label][0]:.6f} {self._data_table[label][1]}"
            )
            val_lineedit.setReadOnly(True)
            val_lineedit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._val_lineedits.append(val_lineedit)
            layout.addWidget(val_lineedit, i, 1)

        layout.addWidget(QLabel("POLL Server"), i + 1, 0)
        layout.addWidget(self._poll_light, i + 1, 1)
        self._poll_light.setSizePolicy(  # type: ignore
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        self.setLayout(layout)

    def _update_widgets(self) -> None:
        """Updates the widgets with the latest values."""
        for i, label in enumerate(self._data_table):
            self._prop_labels[i].setText(label)
            self._val_lineedits[i].setText(
                f"{self._data_table[label][0]:.6f} {self._data_table[label][1]}"
            )

    def poll_server(self) -> None:
        """Polls the server to obtain the latest values."""
        self._poll_light._flash()
        if self._data_table == {}:
            self._data_table = get_vals_from_server()
            self._add_widgets()
        else:
            self._data_table = get_vals_from_server()
            self._update_widgets()


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    em27_monitor = EM27Monitor()

    window.setCentralWidget(em27_monitor)
    window.show()
    app.exec()
