"""Panel and widgets related to monitoring the interferometer."""
from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QLineEdit, QRadioButton


class EM27Monitor(QGroupBox):
    """Widgets to view the EM27 properties."""

    def __init__(self, prop_labels, prop_units) -> None:
        """Creates a sequence of widgets to monitor EM27 physical properties."""
        super().__init__("EM27 SOH Monitor")

        self._prop_labels = deepcopy(prop_labels)
        self._prop_units = deepcopy(prop_units)
        self._psf27_temp_box = QLineEdit(
            self._prop_units[0], readOnly=True, alignment=Qt.AlignCenter
        )
        self._cryo_temp_box = QLineEdit(
            self._prop_units[1], readOnly=True, alignment=Qt.AlignCenter
        )
        self._bb_hum_box = QLineEdit(
            self._prop_units[2], readOnly=True, alignment=Qt.AlignCenter
        )
        self._src_temp_box = QLineEdit(
            self._prop_units[3], readOnly=True, alignment=Qt.AlignCenter
        )
        self._aux_volt_box = QLineEdit(
            self._prop_units[4], readOnly=True, alignment=Qt.AlignCenter
        )
        self._aux_current_box = QLineEdit(
            self._prop_units[5], readOnly=True, alignment=Qt.AlignCenter
        )
        self._laser_current_box = QLineEdit(
            self._prop_units[6], readOnly=True, alignment=Qt.AlignCenter
        )
        self._poll_server_indicator = QRadioButton()

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:
        """Creates the widgets for the EM27 properties.

        Args:

        Returns:
            QGridLayout: The layout with the widgets.
        """
        layout = QGridLayout()

        # Add labels for properties to monitor
        for i, label in enumerate(self._prop_labels):
            layout.addWidget(QLabel(label), i, 0)

        # Add boxes for values of properties to monitor
        layout.addWidget(self._psf27_temp_box, 0, 1)
        layout.addWidget(self._cryo_temp_box, 1, 1)
        layout.addWidget(self._bb_hum_box, 2, 1)
        layout.addWidget(self._src_temp_box, 3, 1)
        layout.addWidget(self._aux_volt_box, 4, 1)
        layout.addWidget(self._aux_current_box, 5, 1)
        layout.addWidget(self._laser_current_box, 6, 1)
        layout.addWidget(self._poll_server_indicator, 7, 1)

        self._poll_server_indicator.clicked.connect(self.poll_server)

        return layout

    def set_psf27_temp(self, val):
        """Sets the PSF27 temperature text box.

        Args:
        val: value polled from server
        """
        self._psf27_temp_box.setText("%.6f deg C" % val)
        return

    def set_cryo_temp(self, val):
        """Sets the cryo temperature text box.

        Args:
        val: value polled from server
        """
        self._cryo_temp_box.setText("%.6f K" % val)
        return

    def set_bb_hum(self, val):
        """Sets the blackbody humidity text box.

        Args:
        val: value polled from server
        """
        self._bb_hum_box.setText("%.6f %%" % val)
        return

    def set_src_temp(self, val):
        """Sets the source temperature text box.

        Args:
        val: value polled from server
        """
        self._src_temp_box.setText("%.6f deg C" % val)
        return

    def set_aux_volt(self, val):
        """Sets the AUX voltage text box.

        Args:
        val: value polled from server
        """
        self._aux_volt_box.setText("%.6f V" % val)
        return

    def set_aux_current(self, val):
        """Sets the AUX current text box.

        Args:
        val: value polled from server
        """
        self._aux_current_box.setText("%.6f A" % val)
        return

    def set_laser_current(self, val):
        """Sets the laser current text box.

        Args:
        val: value polled from server
        """
        self._laser_current_box.setText("%.6f A" % val)
        return

    def poll_server(self):
        """Polls the server, turns on indicator, sets values, turns off indicator.

        Args:
        Returns:
        """
        # Turn light on

        # Get values

        # Turn light off

        # Set values
        self.set_psf27_temp(28.151062)
        self.set_cryo_temp(0.0)
        self.set_bb_hum(2.463968)
        self.set_src_temp(70.007156)
        self.set_aux_volt(6.285875)
        self.set_aux_current(0.910230)
        self.set_laser_current(0.583892)

        return


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

    window.setCentralWidget()
    window.show()
    app.exec()
