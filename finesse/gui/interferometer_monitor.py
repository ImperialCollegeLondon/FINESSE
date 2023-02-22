"""Panel and widgets related to monitoring the interferometer."""
from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit

from .led_icons import LEDIcon


def get_vals_from_server():
    """Placeholder function for retrieving interferometer properties.

    Returns:
        A dictionary containing the physical properties being monitored
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
    """Widgets to view the EM27 properties."""

    def __init__(self, prop_labels, prop_units) -> None:
        """Creates a sequence of widgets to view properties monitored by the EM27."""
        super().__init__("EM27 SOH Monitor")

        self._prop_labels = deepcopy(prop_labels)
        self._prop_units = deepcopy(prop_units)

        self._psf27_temp_box = QLineEdit(self._prop_units[0])
        self._psf27_temp_box.setReadOnly(True)
        self._psf27_temp_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._cryo_temp_box = QLineEdit(self._prop_units[1])
        self._cryo_temp_box.setReadOnly(True)
        self._cryo_temp_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._bb_hum_box = QLineEdit(self._prop_units[2])
        self._bb_hum_box.setReadOnly(True)
        self._bb_hum_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._src_temp_box = QLineEdit(self._prop_units[3])
        self._src_temp_box.setReadOnly(True)
        self._src_temp_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._aux_volt_box = QLineEdit(self._prop_units[4])
        self._aux_volt_box.setReadOnly(True)
        self._aux_volt_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._aux_current_box = QLineEdit(self._prop_units[5])
        self._aux_current_box.setReadOnly(True)
        self._aux_current_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._laser_current_box = QLineEdit(self._prop_units[6])
        self._laser_current_box.setReadOnly(True)
        self._laser_current_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._poll_light = LEDIcon.create_poll_icon()

        layout = self._create_controls()

        self._poll_light.setSizePolicy(self._laser_current_box.sizePolicy())

        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:
        """Creates the widgets for the EM27 properties.

        Returns:
            QGridLayout: The layout with the widgets.
        """
        layout = QGridLayout()

        # Add labels for properties to monitor
        for i, label in enumerate(self._prop_labels):
            layout.addWidget(QLabel(label), i, 0)

        # Add boxes to show monitored properties' values
        layout.addWidget(self._psf27_temp_box, 0, 1)
        layout.addWidget(self._cryo_temp_box, 1, 1)
        layout.addWidget(self._bb_hum_box, 2, 1)
        layout.addWidget(self._src_temp_box, 3, 1)
        layout.addWidget(self._aux_volt_box, 4, 1)
        layout.addWidget(self._aux_current_box, 5, 1)
        layout.addWidget(self._laser_current_box, 6, 1)
        layout.addWidget(self._poll_light, 7, 1)

        return layout

    def set_psf27_temp(self, val: tuple[str, float]) -> None:
        """Sets the PSF27 temperature text box.

        Args:
            val: value polled from server
        """
        self._psf27_temp_box.setText(f"{val[0]:.6f} {val[1]}")

    def set_cryo_temp(self, val: tuple[str, float]) -> None:
        """Sets the cryo temperature text box.

        Args:
            val: value polled from server
        """
        self._cryo_temp_box.setText(f"{val[0]:.6f} {val[1]}")

    def set_bb_hum(self, val: tuple[str, float]) -> None:
        """Sets the blackbody humidity text box.

        Args:
            val: value polled from server
        """
        self._bb_hum_box.setText(f"{val[0]:.6f} {val[1]}")

    def set_src_temp(self, val: tuple[str, float]) -> None:
        """Sets the source temperature text box.

        Args:
            val: value polled from server
        """
        self._src_temp_box.setText(f"{val[0]:.6f} {val[1]}")

    def set_aux_volt(self, val: tuple[str, float]) -> None:
        """Sets the AUX voltage text box.

        Args:
            val: value polled from server
        """
        self._aux_volt_box.setText(f"{val[0]:.6f} {val[1]}")

    def set_aux_current(self, val: tuple[str, float]) -> None:
        """Sets the AUX current text box.

        Args:
            val: value polled from server
        """
        self._aux_current_box.setText(f"{val[0]:.6f} {val[1]}")

    def set_laser_current(self, val: tuple[str, float]) -> None:
        """Sets the laser current text box.

        Args:
            val: value polled from server
        """
        self._laser_current_box.setText(f"{val[0]:.6f} {val[1]}")

    def poll_server(self) -> None:
        """Polls the server, turns on indicator, sets values, turns off indicator."""
        self._poll_light._turn_on()

        data_table = get_vals_from_server()

        self._poll_light._turn_off()

        self.set_psf27_temp(data_table["PSF27 Temp"])
        self.set_cryo_temp(data_table["Cryo Temp"])
        self.set_bb_hum(data_table["Blackbody Hum"])
        self.set_src_temp(data_table["Source Temp"])
        self.set_aux_volt(data_table["Aux Volt"])
        self.set_aux_current(data_table["Aux Curr"])
        self.set_laser_current(data_table["Laser Curr"])


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    prop_labels = [
        "PSF27 Temp",
        "Cryo Temp",
        "Blackbody Hum",
        "Source Temp",
        "AUX Volt",
        "AUX Curr",
        "Laser Curr",
        "POLL Server",
    ]
    prop_units = [
        "deg. C",
        "deg. K",
        "%",
        "deg. C",
        "V",
        "A",
        "A",
        None,
    ]
    em27_monitor = EM27Monitor(prop_labels, prop_units)

    window.setCentralWidget(em27_monitor)
    window.show()
    app.exec()