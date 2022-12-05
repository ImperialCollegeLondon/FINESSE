"""Panel and widgets related to temperature monitoring."""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
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
        """Creates a panel with a graph to monitor the hot and cold bb temperatures."""
        super().__init__("BB Monitor")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:
        """Creates the overall layout for the panel.

        Returns:
            QGridLayout: The layout containing the figure.
        """
        layout = QGridLayout()
        self._create_figure()

        layout.addWidget(self._canvas, 0, 0)

        return layout

    def _create_figure(self) -> None:
        """Creates the matplotlib figure to be contained within the panel.

        Returns:
            None
        """
        self._figure, self._ax1 = plt.subplots()
        self._canvas = FigureCanvasQTAgg(self._figure)

        t = [1040, 1050, 1060, 1070, 1080, 1090, 1100]
        hot_bb_temp = [55, 57.5, 60, 62.5, 65, 67.5, 70]
        cold_bb_temp = [1, 1.1, 1.15, 1.2, 1.3, 1.4, 1.5]

        self._bb_hot_line = self._ax1.plot(t, hot_bb_temp, color=[0, 1, 0])
        self._ax1.set_xlabel("")
        self._ax1.set_ylabel("HOT BB", color=[0, 1, 0])
        self._ax1.set_xlim([1045, 1101.4])
        self._ax1.set_ylim([20, 80])

        self._ax2 = self._ax1.twinx()
        self._bb_cold_line = self._ax2.plot(t, cold_bb_temp, color=[1, 1, 0])
        self._ax2.set_ylabel("COLD BB", color=[1, 1, 0])
        self._ax2.set_ylim([0, 10])

        self._canvas.draw()

    def _update_figure(self) -> None:  # , x, y) -> None:
        """Updates the matplotlib figure to be contained within the panel.

        Args:
            #x: time
            #y: temperature
            # probably won't be inputs since obtainable from elsewhere
        Returns:
            None
        """
        xdata = list(self._bb_hot_line[0].get_xdata())
        y1data = list(self._bb_hot_line[0].get_ydata())
        y2data = list(self._bb_cold_line[0].get_ydata())

        xdata.pop(0)
        y1data.pop(0)
        y2data.pop(0)

        x = xdata[-1] + 10

        # Basic RNG for testing
        y1 = (60 * y1data[-1] + 50) % 70
        y2 = (5 * y2data[-1] + 1) % 8

        xdata.append(x)
        y1data.append(y1)
        y2data.append(y2)

        self._bb_hot_line[0].set_xdata(xdata)
        self._bb_hot_line[0].set_ydata(y1data)
        self._bb_cold_line[0].set_xdata(xdata)
        self._bb_cold_line[0].set_ydata(y2data)

        self._ax1.relim()
        self._ax2.xaxis.axes.relim()
        self._ax1.autoscale()
        self._ax2.xaxis.axes.autoscale()
        self._ax2.set_ylim([self._ax2.get_ylim()[0], 2 * self._ax2.get_ylim()[1]])
        self._canvas.draw()


class DP9800(QGroupBox):
    """Widgets to view the DP9800 properties."""

    def __init__(self) -> None:
        """Creates the widgets to monitor DP9800.

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
            wid.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(wid, 0, i)

        self._ch1 = QLineEdit()
        self._ch1.setReadOnly(True)
        layout.addWidget(self._ch1, 1, 1)

        self._ch2 = QLineEdit()
        self._ch2.setReadOnly(True)
        layout.addWidget(self._ch2, 1, 2)

        self._ch3 = QLineEdit()
        self._ch3.setReadOnly(True)
        layout.addWidget(self._ch3, 1, 3)

        self._ch4 = QLineEdit()
        self._ch4.setReadOnly(True)
        layout.addWidget(self._ch4, 1, 4)

        self._ch5 = QLineEdit()
        self._ch5.setReadOnly(True)
        layout.addWidget(self._ch5, 1, 5)

        self._ch6 = QLineEdit()
        self._ch6.setReadOnly(True)
        layout.addWidget(self._ch6, 1, 6)

        self._ch7 = QLineEdit()
        self._ch7.setReadOnly(True)
        layout.addWidget(self._ch7, 1, 7)

        self._ch8 = QLineEdit()
        self._ch8.setReadOnly(True)
        layout.addWidget(self._ch8, 1, 8)

        wid = QLabel("POLL")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 0, 9, 2, 1)

        self._poll_light = QLabel()
        self._poll_light.setPixmap(QPixmap("./finesse/gui/images/poll_off.png"))
        layout.addWidget(self._poll_light, 0, 10, 2, 1)

        return layout


class TC4820_HOT(QGroupBox):
    """Widgets to view the TC4820 HOT properties."""

    def __init__(self) -> None:
        """Creates the widgets to control and monitor TC4820 HOT.

        Returns:
            None
        """
        super().__init__("TC4820 HOT")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:

        layout = QGridLayout()

        wid = QLabel("CONTROL")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 0, 0)

        wid = QLabel("POWER")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 1, 0)

        wid = QLabel("SET")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 2, 0)

        wid = QLabel("Pt 100")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 0, 2)

        wid = QLabel("POLL")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 0, 4)

        wid = QLabel("ALARM")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 2, 4)

        self._control_val = QLineEdit("70.5")
        self._control_val.setReadOnly(True)
        self._control_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._control_val, 0, 1)

        self._pt100_val = QLineEdit("70.34")  # CH_7?
        self._pt100_val.setReadOnly(True)
        self._pt100_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._pt100_val, 0, 3)

        self._power_slider = QSlider()
        self._power_slider.setOrientation(Qt.Orientation.Horizontal)
        layout.addWidget(self._power_slider, 1, 1, 1, 3)
        layout.addWidget(QLineEdit("40"), 1, 4)

        self._poll_light = QLabel()
        self._poll_light.setPixmap(QPixmap("./finesse/gui/images/poll_off.png"))
        self._alarm_light = QLabel()
        self._alarm_light.setPixmap(QPixmap("./finesse/gui/images/alarm_on.png"))
        layout.addWidget(self._poll_light, 0, 5)
        layout.addWidget(self._alarm_light, 2, 5)

        self._set_sbox = QSpinBox()
        layout.addWidget(self._set_sbox, 2, 1)

        self._update_pbtn = QPushButton("UPDATE")
        layout.addWidget(self._update_pbtn, 2, 3)

        return layout


class TC4820_COLD(QGroupBox):
    """Widgets to view the TC4820 COLD properties.

    Potentially redundant if similar to TC4820 HOT.
    """

    def __init__(self) -> None:
        """Creates the widgets to control and monitor TC4820 COLD.

        Returns:
            None
        """
        super().__init__("TC4820 COLD")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:

        layout = QGridLayout()

        wid = QLabel("CONTROL")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 0, 0)

        wid = QLabel("POWER")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 1, 0)

        wid = QLabel("SET")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 2, 0)

        wid = QLabel("Pt 100")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 0, 2)

        wid = QLabel("POLL")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 0, 4)

        wid = QLabel("ALARM")
        wid.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(wid, 2, 4)

        self._control_val = QLineEdit("31.9")
        self._control_val.setReadOnly(True)
        self._control_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._control_val, 0, 1)

        self._pt100_val = QLineEdit("29.06")  # CH_8?
        self._pt100_val.setReadOnly(True)
        self._pt100_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._pt100_val, 0, 3)

        self._power_slider = QSlider()
        self._power_slider.setOrientation(Qt.Orientation.Horizontal)
        layout.addWidget(self._power_slider, 1, 1, 1, 3)
        layout.addWidget(QLineEdit("0"), 1, 4)

        self._poll_light = QLabel()
        self._poll_light.setPixmap(QPixmap("./finesse/gui/images/poll_on.png"))
        self._alarm_light = QLabel()
        self._alarm_light.setPixmap(QPixmap("./finesse/gui/images/alarm_off.png"))
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
