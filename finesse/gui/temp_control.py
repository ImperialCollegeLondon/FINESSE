"""Panel and widgets related to temperature monitoring."""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QWidget,
)

# plt.style.use("./finesse_gui.style")
plt.rcParams["figure.facecolor"] = "black"
plt.rcParams["axes.facecolor"] = "black"
plt.rcParams["axes.edgecolor"] = "white"
plt.rcParams["text.color"] = "white"
plt.rcParams["xtick.color"] = "white"
plt.rcParams["ytick.color"] = "white"


class BBMonitor(QGroupBox):
    """Widgets to view the temperature properties."""

    def __init__(self) -> None:
        """Creates a figure to monitor the hot and cold blackbody temperatures over time.

        Args:
            None
        """
        super().__init__("BB Monitor")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:
        """Creates the overall layout for the panel.

        Args:
            None

        Returns:
            QGridLayout: The layout containing the figure.
        """
        layout = QGridLayout()
        self._create_figure()

        layout.addWidget(self._canvas, 0, 0)

        return layout

    def _create_figure(self):
        """Creates the matplotlib figure to be contained within the panel.

        Args:
            None

        Returns:
            None
        """
        self._figure, ax1 = plt.subplots()
        self._canvas = FigureCanvas(self._figure)

        t = [1045.5, 1101]
        hot_bb_temp = [55, 70]
        cold_bb_temp = [1, 1.5]

        ax1.plot(t, hot_bb_temp, color=[0, 1, 0])
        ax1.set_xlabel("")
        ax1.set_ylabel("HOT BB", color=[0, 1, 0])
        ax1.set_xlim([1045, 1101.4])
        ax1.set_ylim([20, 80])

        ax2 = ax1.twinx()
        ax2.plot(t, cold_bb_temp, color=[1, 1, 0])
        ax2.set_ylabel("COLD BB", color=[1, 1, 0])
        ax2.set_ylim([0, 10])

        self._canvas.draw()

    def _update_figure(self, x, y):
        """Updates the matplotlib figure to be contained within the panel.

        Args:
            x: time
            y: temperature
        Returns:
            None
        """
        self._canvas.draw()


class DP9800(QGroupBox):
    """Widgets to view the DP9800 properties."""

    def __init__(self) -> None:
        """Creates the widgets to monitor DP9800.

        Args:
            None

        Returns:
            None
        """
        super().__init__("DP9800")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:

        layout = QGridLayout()

        layout.addWidget(QLabel("Pt 100"), 1, 0)
        for i in range(1, 9):
            wid = QLabel("CH_%d" % i)
            wid.setAlignment(Qt.AlignCenter)
            layout.addWidget(wid, 0, i)
            layout.addWidget(
                QLineEdit(), 1, i
            )  # presumably need to store these for access later

        wid = QLabel("POLL")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 0, 9, 2, 1)

        self._poll_light = QLabel()
        self._poll_light.setPixmap(QPixmap("/home/dc2917/Pictures/poll_off.png"))
        layout.addWidget(self._poll_light, 0, 10, 2, 1)

        return layout


class TC4820_HOT(QGroupBox):
    """Widgets to view the TC4820 HOT properties."""

    def __init__(self) -> None:
        """Creates the widgets to control and monitor TC4820 HOT.

        Args:
            None

        Returns:
            None
        """
        super().__init__("TC4820 HOT")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:

        layout = QGridLayout()  # want 6x3

        wid = QLabel("CONTROL")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 0, 0)

        wid = QLabel("POWER")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 1, 0)

        wid = QLabel("SET")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 2, 0)

        wid = QLabel("Pt 100")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 0, 2)

        wid = QLabel("POLL")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 0, 4)

        wid = QLabel("ALARM")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 2, 4)

        self._control_val = QLineEdit("70.5")
        self._control_val.setReadOnly(True)
        self._control_val.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._control_val, 0, 1)

        self._pt100_val = QLineEdit("70.34")  # CH_7?
        self._pt100_val.setReadOnly(True)
        self._pt100_val.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._pt100_val, 0, 3)

        self._power_slider = QSlider(Qt.Horizontal)
        layout.addWidget(self._power_slider, 1, 1, 1, 3)
        layout.addWidget(QLineEdit("40"), 1, 4)

        self._poll_light = QLabel()
        self._poll_light.setPixmap(QPixmap("/home/dc2917/Pictures/poll_off.png"))
        self._alarm_light = QLabel()
        self._alarm_light.setPixmap(QPixmap("/home/dc2917/Pictures/alarm_on.png"))
        layout.addWidget(self._poll_light, 0, 5)
        layout.addWidget(self._alarm_light, 2, 5)

        self._set_sbox = QSpinBox()
        layout.addWidget(self._set_sbox, 2, 1)

        self._update_pbtn = QPushButton("UPDATE")
        layout.addWidget(self._update_pbtn, 2, 3)

        return layout


class TC4820_COLD(QGroupBox):
    """Widgets to view the TC4820 COLD properties."""

    def __init__(self) -> None:
        """Creates the widgets to control and monitor TC4820 COLD.

        Args:
            None

        Returns:
            None
        """
        super().__init__("TC4820 COLD")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:

        layout = QGridLayout()  #

        wid = QLabel("CONTROL")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 0, 0)

        wid = QLabel("POWER")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 1, 0)

        wid = QLabel("SET")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 2, 0)

        wid = QLabel("Pt 100")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 0, 2)

        wid = QLabel("POLL")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 0, 4)

        wid = QLabel("ALARM")
        wid.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(wid, 2, 4)

        self._control_val = QLineEdit("31.9")
        self._control_val.setReadOnly(True)
        self._control_val.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._control_val, 0, 1)

        self._pt100_val = QLineEdit("29.06")  # CH_8?
        self._pt100_val.setReadOnly(True)
        self._pt100_val.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._pt100_val, 0, 3)

        self._power_slider = QSlider(Qt.Horizontal)
        layout.addWidget(self._power_slider, 1, 1, 1, 3)
        layout.addWidget(QLineEdit("0"), 1, 4)

        self._poll_light = QLabel()
        self._poll_light.setPixmap(QPixmap("/home/dc2917/Pictures/poll_on.png"))
        self._alarm_light = QLabel()
        self._alarm_light.setPixmap(QPixmap("/home/dc2917/Pictures/alarm_off.png"))
        layout.addWidget(self._poll_light, 0, 5)
        layout.addWidget(self._alarm_light, 2, 5)

        self._set_sbox = QSpinBox()
        layout.addWidget(self._set_sbox, 2, 1)

        self._update_pbtn = QPushButton("UPDATE")
        layout.addWidget(self._update_pbtn, 2, 3)

        return layout


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()

    layout = QGridLayout()

    bb_monitor = BBMonitor()
    dp9800 = DP9800()
    tc4820_hot = TC4820_HOT()
    tc4820_cold = TC4820_COLD()

    layout.addWidget(bb_monitor, 0, 0, 1, 0)
    layout.addWidget(dp9800, 1, 0, 1, 0)
    layout.addWidget(tc4820_hot, 2, 0)
    layout.addWidget(tc4820_cold, 2, 1)

    centralWidget = QWidget()
    centralWidget.setLayout(layout)

    window.setCentralWidget(centralWidget)
    window.show()
    app.exec()
