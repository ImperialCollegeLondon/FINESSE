"""Panel and widgets related to temperature monitoring."""
from datetime import datetime
from decimal import Decimal
from functools import partial

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from pubsub import pub
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QWidget,
)

from ..config import TEMPERATURE_CONTROLLER_TOPIC, TEMPERATURE_MONITOR_TOPIC
from .led_icons import LEDIcon
from .serial_device_panel import SerialDevicePanel


class TemperaturePlot(QGroupBox):
    """Widgets to view the temperature properties."""

    def __init__(self) -> None:
        """Creates a panel with a graph to monitor the blackbody temperatures."""
        super().__init__("BB Monitor")

        layout = self._create_controls()
        self.setLayout(layout)

        pub.subscribe(
            self._plot_bb_temps, f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response"
        )

    def _create_controls(self) -> QGridLayout:
        """Creates the overall layout for the panel.

        Returns:
            QGridLayout: The layout containing the figure.
        """
        layout = QGridLayout()
        self._btns = {"hot": QPushButton("Hot BB"), "cold": QPushButton("Cold BB")}
        self._btns["hot"].clicked.connect(  # type: ignore
            partial(self._toggle_axis_visibility, name="hot")
        )
        self._btns["cold"].clicked.connect(  # type: ignore
            partial(self._toggle_axis_visibility, name="cold")
        )
        self._create_figure()
        self._canvas.setMinimumSize(QSize(640, 120))
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding
        )

        layout.addWidget(self._btns["hot"], 0, 0)
        layout.addWidget(self._btns["cold"], 1, 0)
        layout.addWidget(self._canvas, 0, 1, 2, 1)

        return layout

    def _create_figure(self) -> None:
        """Creates the matplotlib figure to be contained within the panel."""
        self._figure, ax = plt.subplots(constrained_layout=True)
        self._ax = {"hot": ax}
        self._canvas = FigureCanvasQTAgg(self._figure)

        self._figure_num_pts = 10
        t = [None] * self._figure_num_pts
        hot_bb_temp = [None] * self._figure_num_pts
        cold_bb_temp = [None] * self._figure_num_pts

        colours = plt.rcParams["axes.prop_cycle"]
        hot_colour = colours.by_key()["color"][0]
        cold_colour = colours.by_key()["color"][1]

        self._ax["hot"].plot(
            t, hot_bb_temp, color=hot_colour, marker="x", linestyle="-"
        )
        self._ax["hot"].set_ylabel("HOT BB", color=hot_colour)

        self._ax["cold"] = self._ax["hot"].twinx()
        self._ax["cold"].plot(
            t, cold_bb_temp, color=cold_colour, marker="x", linestyle="-"
        )
        self._ax["cold"].set_ylabel("COLD BB", color=cold_colour)

        self._canvas.draw()

    def _toggle_axis_visibility(self, name: str) -> None:
        """Shows or hides individual blackbody temperature plots.

        Args:
            name: the name of the blackbody whose data visibility is toggled
        """
        state = self._ax[name].yaxis.get_visible()
        self._btns[name].setFlat(state)
        self._ax[name].yaxis.set_visible(not state)
        self._ax[name].lines[0].set_visible(not state)
        self._canvas.draw()

    def _update_figure(
        self, new_time: float, new_hot_data: Decimal, new_cold_data: Decimal
    ) -> None:
        """Updates the matplotlib figure to be contained within the panel.

        Args:
            new_time: the time at which the new data were retrieved
            new_hot_data: the new temperature of the hot blackbody
            new_cold_data: the new temperature of the cold blackbody
        """
        time = list(self._ax["hot"].lines[0].get_xdata())
        hot_data = list(self._ax["hot"].lines[0].get_ydata())
        cold_data = list(self._ax["cold"].lines[0].get_ydata())

        time.pop(0)
        hot_data.pop(0)
        cold_data.pop(0)

        time.append(new_time)
        hot_data.append(new_hot_data)
        cold_data.append(new_cold_data)

        self._ax["hot"].lines[0].set_xdata(time)
        self._ax["hot"].lines[0].set_ydata(hot_data)
        self._ax["cold"].lines[0].set_xdata(time)
        self._ax["cold"].lines[0].set_ydata(cold_data)

        self._ax["hot"].relim()
        self._ax["cold"].relim()
        self._ax["hot"].autoscale()
        self._ax["cold"].autoscale()
        self._ax["cold"].set_ylim(  # Confines "cold" line to lower half of plot
            [self._ax["cold"].get_ylim()[0], 2 * self._ax["cold"].get_ylim()[1]]
        )

        xticks = self._ax["hot"].get_xticks()
        xticklabels = [""] * len(xticks)
        for i in range(len(xticks)):
            t = datetime.fromtimestamp(xticks[i])
            xticklabels[i] = t.strftime("%H:%M:%S")
        self._ax["hot"].set_xticklabels(xticklabels)

        self._canvas.draw()

    def _plot_bb_temps(self, time: float, temperatures: list[Decimal]) -> None:
        """Extract blackbody temperatures from DP9800 data and plot them.

        Args:
            time: the time that the temperatures were read
            temperatures: the list of temperatures measured by the DP9800
        """
        hot_bb_temp = temperatures[6]
        cold_bb_temp = temperatures[7]

        self._update_figure(time, hot_bb_temp, cold_bb_temp)


class DP9800Controls(SerialDevicePanel):
    """Widgets to view the DP9800 properties."""

    def __init__(self, num_channels: int = 8, poll_interval: int = 2000) -> None:
        """Creates the widgets to monitor DP9800.

        Args:
            num_channels: Number of Pt 100 channels being monitored
            poll_interval: Period with which to update the values (in seconds)
        """
        super().__init__(TEMPERATURE_MONITOR_TOPIC, "DP9800")

        self._num_channels = num_channels
        self._poll_interval = poll_interval

        layout = self._create_controls()
        self.setLayout(layout)

        pub.subscribe(self._begin_polling, f"serial.{TEMPERATURE_MONITOR_TOPIC}.opened")
        pub.subscribe(self._end_polling, f"serial.{TEMPERATURE_MONITOR_TOPIC}.close")
        pub.subscribe(
            self._update_pt100s, f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response"
        )

    def _create_controls(self) -> QGridLayout:
        """Creates the overall layout for the panel.

        Returns:
            QGridLayout: The layout containing the figure.
        """
        layout = QGridLayout()

        layout.addWidget(QLabel("Pt 100"), 1, 0)
        self._channels = []
        for i in range(self._num_channels):
            channel_label = QLabel(f"CH_{i+1}")
            channel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(channel_label, 0, i + 1)

            channel_tbox = QLineEdit()
            channel_tbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
            channel_tbox.setReadOnly(True)
            self._channels.append(channel_tbox)
            layout.addWidget(channel_tbox, 1, i + 1)

        poll_label = QLabel("POLL")
        poll_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(poll_label, 0, 9, 2, 1)

        self._poll_light = LEDIcon.create_poll_icon()
        self._poll_light.timer.setInterval(self._poll_interval)
        self._poll_light.timer.timeout.connect(self._poll_dp9800)  # type: ignore
        layout.addWidget(self._poll_light, 0, 10, 2, 1)

        return layout

    def _begin_polling(self) -> None:
        """Initiate polling the DP9800 device."""
        self._poll_light.timer.start()

    def _end_polling(self) -> None:
        """Terminate polling the DP9800 device."""
        self._poll_light.timer.stop()

    def _poll_dp9800(self) -> None:
        """Polls the device to obtain the latest values."""
        self._poll_light.flash()
        pub.sendMessage(f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.request")

    def _update_pt100s(self, temperatures: list[Decimal], time: float) -> None:
        """Display the latest Pt 100 temperatures.

        Args:
            temperatures: the temperatures retrieved from the DP9800
            time: the time that the temperatures were retrieved
        """
        for channel, temperature in zip(self._channels, temperatures):
            channel.setText(f"{temperature: .2f}")


class TC4820Controls(SerialDevicePanel):
    """Widgets to view the TC4820 properties."""

    def __init__(self, name: str) -> None:
        """Creates the widgets to control and monitor a TC4820.

        Args:
            name: Name of the blackbody the TC4820 is controlling
        """
        super().__init__(
            f"{TEMPERATURE_CONTROLLER_TOPIC}.{name}_bb", f"TC4820 {name.upper()}"
        )

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QGridLayout:
        """Creates the overall layout for the panel.

        Returns:
            QGridLayout: The layout containing the figure.
        """
        layout = QGridLayout()

        align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        control_label = QLabel("CONTROL")
        control_label.setAlignment(align)
        layout.addWidget(control_label, 0, 0)

        power_label = QLabel("POWER")
        power_label.setAlignment(align)
        layout.addWidget(power_label, 1, 0)

        set_label = QLabel("SET")
        set_label.setAlignment(align)
        layout.addWidget(set_label, 2, 0)

        pt100_label = QLabel("Pt 100")
        pt100_label.setAlignment(align)
        layout.addWidget(pt100_label, 0, 2)

        poll_label = QLabel("POLL")
        poll_label.setAlignment(align)
        layout.addWidget(poll_label, 0, 4)

        alarm_label = QLabel("ALARM")
        alarm_label.setAlignment(align)
        layout.addWidget(alarm_label, 2, 4)

        self._control_val = QLineEdit()
        self._control_val.setReadOnly(True)
        self._control_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._control_val, 0, 1)

        self._pt100_val = QLineEdit()
        self._pt100_val.setReadOnly(True)
        self._pt100_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._pt100_val, 0, 3)

        self._power_bar = QProgressBar()
        self._power_bar.setTextVisible(False)
        self._power_bar.setOrientation(Qt.Orientation.Horizontal)
        layout.addWidget(self._power_bar, 1, 1, 1, 3)
        layout.addWidget(QLineEdit(), 1, 4)

        self._poll_light = LEDIcon.create_poll_icon()
        self._alarm_light = LEDIcon.create_alarm_icon()
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

    temperature_plot = TemperaturePlot()
    dp9800 = DP9800Controls()
    tc4820_hot = TC4820Controls("hot")
    tc4820_cold = TC4820Controls("cold")

    layout.addWidget(temperature_plot, 0, 0, 1, 0)
    layout.addWidget(dp9800, 1, 0, 1, 0)
    layout.addWidget(tc4820_hot, 2, 0)
    layout.addWidget(tc4820_cold, 2, 1)

    centralWidget = QWidget()
    centralWidget.setLayout(layout)

    window.setCentralWidget(centralWidget)
    window.show()
    app.exec()
