"""Panel and widgets related to monitoring the interferometer."""
from copy import deepcopy
from importlib import resources

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit

img_files = resources.files("finesse.gui.images")
poll_on_img_data = img_files.joinpath("poll_on.png").read_bytes()
poll_off_img_data = img_files.joinpath("poll_off.png").read_bytes()
poll_on_img = QImage.fromData(poll_on_img_data)
poll_off_img = QImage.fromData(poll_off_img_data)


def get_vals_from_server():
    """Placeholder function for retrieving interferometer properties.

    Returns:
        A list of values of the physical properties being monitored
    """
    psf27_temp = 28.151062
    cryo_temp = 0.0
    bb_hum = 2.463968
    src_temp = 70.007156
    aux_volt = 6.285875
    aux_current = 0.910230
    laser_current = 0.583892
    return [
        psf27_temp,
        cryo_temp,
        bb_hum,
        src_temp,
        aux_volt,
        aux_current,
        laser_current,
    ]


class EM27Monitor(QGroupBox):
    """Widgets to view the EM27 properties."""

    def __init__(self, prop_labels, prop_units) -> None:
        """Creates a sequence of widgets to monitor EM27 physical properties."""
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

        self._poll_light = QLabel()
        self._poll_light.setPixmap(QPixmap(poll_off_img))

        layout = self._create_controls()
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

    def set_psf27_temp(self, val: float) -> None:
        """Sets the PSF27 temperature text box.

        Args:
            val: value polled from server
        """
        self._psf27_temp_box.setText("%.6f %s" % (val, self._prop_units[0]))

    def set_cryo_temp(self, val: float) -> None:
        """Sets the cryo temperature text box.

        Args:
            val: value polled from server
        """
        self._cryo_temp_box.setText("%.6f %s" % (val, self._prop_units[1]))

    def set_bb_hum(self, val: float) -> None:
        """Sets the blackbody humidity text box.

        Args:
            val: value polled from server
        """
        self._bb_hum_box.setText("%.6f %s" % (val, self._prop_units[2]))

    def set_src_temp(self, val: float) -> None:
        """Sets the source temperature text box.

        Args:
            val: value polled from server
        """
        self._src_temp_box.setText("%.6f %s" % (val, self._prop_units[3]))

    def set_aux_volt(self, val: float) -> None:
        """Sets the AUX voltage text box.

        Args:
            val: value polled from server
        """
        self._aux_volt_box.setText("%.6f %s" % (val, self._prop_units[4]))

    def set_aux_current(self, val: float) -> None:
        """Sets the AUX current text box.

        Args:
            val: value polled from server
        """
        self._aux_current_box.setText("%.6f %s" % (val, self._prop_units[0]))

    def set_laser_current(self, val: float) -> None:
        """Sets the laser current text box.

        Args:
            val: value polled from server
        """
        self._laser_current_box.setText("%.6f %s" % (val, self._prop_units[0]))

    def poll_server(self) -> None:
        """Polls the server, turns on indicator, sets values, turns off indicator."""
        # Turn light on
        self._poll_light.setPixmap(QPixmap(poll_on_img))

        # Get values
        [
            psf27_temp,
            cryo_temp,
            bb_hum,
            src_temp,
            aux_volt,
            aux_current,
            laser_current,
        ] = get_vals_from_server()

        # Turn light off
        self._poll_light.setPixmap(QPixmap(poll_off_img))

        # Set values
        self.set_psf27_temp(psf27_temp)
        self.set_cryo_temp(cryo_temp)
        self.set_bb_hum(bb_hum)
        self.set_src_temp(src_temp)
        self.set_aux_volt(aux_volt)
        self.set_aux_current(aux_current)
        self.set_laser_current(laser_current)


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
        "AUX Current",
        "Laser Current",
        "POLL Server",
    ]
    prop_units = [
        "deg C",
        "K",
        "%",
        "deg C",
        "V",
        "A",
        "A",
        None,
    ]
    em27_monitor = EM27Monitor(prop_labels, prop_units)

    window.setCentralWidget(em27_monitor)
    window.show()
    app.exec()
