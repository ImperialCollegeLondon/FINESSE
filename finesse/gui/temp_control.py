"""Panel and widgets related to temperature monitoring."""
from datetime import datetime
from decimal import Decimal
from functools import partial

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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

from ..config import (
    NUM_TEMPERATURE_MONITOR_CHANNELS,
    TEMPERATURE_CONTROLLER_POLL_INTERVAL,
    TEMPERATURE_CONTROLLER_TOPIC,
    TEMPERATURE_MONITOR_COLD_BB_IDX,
    TEMPERATURE_MONITOR_HOT_BB_IDX,
    TEMPERATURE_MONITOR_POLL_INTERVAL,
    TEMPERATURE_MONITOR_TOPIC,
    TEMPERATURE_PLOT_TIME_RANGE,
)
from .led_icons import LEDIcon
from .serial_device_panel import SerialDevicePanel


class TemperaturePlot(QGroupBox):
    """Widgets to view the temperature properties."""

    def __init__(self) -> None:
        """Creates a panel with a graph to monitor the blackbody temperatures."""
        super().__init__("BB Monitor")

        layout = self._create_controls()
        self.setLayout(layout)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.MinimumExpanding,
        )

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
        self._btns["hot"].setCheckable(True)
        self._btns["cold"].setCheckable(True)
        self._btns["hot"].setChecked(True)
        self._btns["cold"].setChecked(True)
        self._btns["hot"].clicked.connect(
            partial(self._toggle_axis_visibility, name="hot")
        )
        self._btns["cold"].clicked.connect(
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
        self._canvas.mpl_connect("resize_event", self._resize_plot)

        self._figure_num_pts = int(
            TEMPERATURE_PLOT_TIME_RANGE / TEMPERATURE_MONITOR_POLL_INTERVAL
        )
        t = [None] * self._figure_num_pts
        hot_bb_temp = [None] * self._figure_num_pts
        cold_bb_temp = [None] * self._figure_num_pts

        hot_colour = "r"
        cold_colour = "b"

        self._ax["hot"].plot(t, hot_bb_temp, color=hot_colour, linestyle="-")
        self._ax["hot"].set_ylabel("HOT BB", color=hot_colour)

        max_ticks = 8
        self._ax["hot"].xaxis.set_major_locator(ticker.MaxNLocator(nbins=max_ticks - 1))
        self._ax["hot"].xaxis.set_major_formatter(
            ticker.FuncFormatter(self._xtick_format_fcn)
        )

        self._ax["cold"] = self._ax["hot"].twinx()
        self._ax["cold"].plot(t, cold_bb_temp, color=cold_colour, linestyle="-")
        self._ax["cold"].set_ylabel("COLD BB", color=cold_colour)

        self._canvas.draw()

    def _toggle_axis_visibility(self, name: str) -> None:
        """Shows or hides individual blackbody temperature plots.

        Args:
            name: the name of the blackbody whose data visibility is toggled
        """
        state = self._btns[name].isChecked()
        self._ax[name].yaxis.set_visible(state)
        self._ax[name].lines[0].set_visible(state)

        self._make_axes_sensible()
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

        self._make_axes_sensible()

        self._canvas.draw()

    def _xtick_format_fcn(self, val: float, loc: int) -> str:
        """Convert x axis tick labels from timestamp to clock format.

        Args:
            val: value of the tick whose label is being formatted
            loc: location of the tick on the axis

        Returns:
            formatted string to display as x tick label
        """
        return datetime.fromtimestamp(val).strftime("%H:%M:%S")

    def _make_axes_sensible(self) -> None:
        """Rescales the y axes for the the blackbody temperatures."""
        # Rescale limits to account for new data
        self._ax["hot"].relim()
        self._ax["cold"].relim()
        self._ax["hot"].autoscale()
        self._ax["cold"].autoscale()

        ylim_hot = self._ax["hot"].get_ylim()
        ylim_cold = self._ax["cold"].get_ylim()

        # Confine "hot" line to upper region of plot if "cold" line also visible
        if self._ax["cold"].yaxis.get_visible():
            self._ax["hot"].set_ylim([ylim_hot[0] - 5, ylim_hot[1] + 1])

        # Confine "cold" line to lower region of plot if "hot" line also visible
        if self._ax["hot"].yaxis.get_visible():
            self._ax["cold"].set_ylim([ylim_cold[0] - 1, ylim_cold[1] + 5])

    def _resize_plot(self, event) -> None:
        """Custom resize function for matplotlib figurecanvas."""
        if not self._canvas.isVisible():
            self._canvas_pos_offset = [self._canvas.x(), self._canvas.y()]
            self._canvas_size_diff = [
                self.geometry().width() - self._canvas.width(),
                self.geometry().height() - self._canvas.height(),
            ]

        self._canvas.move(self._canvas_pos_offset[0], self._canvas_pos_offset[1])

        new_width = self.width() - self._canvas_size_diff[0]
        new_height = self.height() - self._canvas_size_diff[1]
        self._canvas.resize(new_width, new_height)
        self._canvas.figure.set_figwidth(new_width / self._canvas.figure.get_dpi())
        self._canvas.figure.set_figheight(new_height / self._canvas.figure.get_dpi())

    def _plot_bb_temps(self, time: datetime, temperatures: list[Decimal]) -> None:
        """Extract blackbody temperatures from DP9800 data and plot them.

        Args:
            time: the time that the temperatures were read
            temperatures: the list of temperatures measured by the DP9800
        """
        hot_bb_temp = temperatures[TEMPERATURE_MONITOR_HOT_BB_IDX]
        cold_bb_temp = temperatures[TEMPERATURE_MONITOR_COLD_BB_IDX]

        self._update_figure(time.timestamp(), hot_bb_temp, cold_bb_temp)


class DP9800Controls(SerialDevicePanel):
    """Widgets to view the DP9800 properties."""

    def __init__(self, num_channels: int = NUM_TEMPERATURE_MONITOR_CHANNELS) -> None:
        """Creates the widgets to monitor DP9800.

        Args:
            num_channels: Number of Pt 100 channels being monitored
        """
        super().__init__(TEMPERATURE_MONITOR_TOPIC, "DP9800")

        self._num_channels = num_channels
        self._poll_interval = 1000 * TEMPERATURE_MONITOR_POLL_INTERVAL

        layout = self._create_controls()
        self.setLayout(layout)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

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
        self._poll_light.timer.timeout.connect(self._poll_dp9800)
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

    def _update_pt100s(self, temperatures: list[Decimal], time: datetime) -> None:
        """Display the latest Pt 100 temperatures.

        Args:
            temperatures: the temperatures retrieved from the DP9800
            time: the time that the temperatures were retrieved
        """
        for channel, temperature in zip(self._channels, temperatures):
            channel.setText(f"{temperature: .2f}")


class TC4820Controls(SerialDevicePanel):
    """Widgets to view the TC4820 properties."""

    def __init__(self, name: str, temperature_idx: int) -> None:
        """Creates the widgets to control and monitor a TC4820.

        Args:
            name: Name of the blackbody the TC4820 is controlling
            temperature_idx: Index of the blackbody on the temperature monitor
        """
        super().__init__(
            f"{TEMPERATURE_CONTROLLER_TOPIC}.{name}_bb", f"TC4820 {name.upper()}"
        )
        self._name = name
        self._poll_interval = 1000 * TEMPERATURE_CONTROLLER_POLL_INTERVAL
        self._temperature_idx = temperature_idx

        layout = self._create_controls()
        self.setLayout(layout)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )

        pub.subscribe(
            self._begin_polling,
            f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{name}_bb.opened",
        )
        pub.subscribe(
            self._end_polling, f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{name}_bb.close"
        )
        pub.subscribe(
            self._update_controls,
            f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{name}_bb.response",
        )
        pub.subscribe(
            self._update_pt100, f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response"
        )

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

        self._power_label = QLineEdit()
        self._power_label.setReadOnly(True)
        layout.addWidget(self._power_label, 1, 4)

        self._poll_light = LEDIcon.create_poll_icon()
        self._poll_light.timer.timeout.connect(self._poll_tc4820)
        self._alarm_light = LEDIcon.create_alarm_icon()
        layout.addWidget(self._poll_light, 0, 5)
        layout.addWidget(self._alarm_light, 2, 5)

        self._set_sbox = QSpinBox()
        layout.addWidget(self._set_sbox, 2, 1)

        self._update_pbtn = QPushButton("UPDATE")
        self._update_pbtn.setCheckable(True)
        self._update_pbtn.clicked.connect(self._on_update_clicked)
        layout.addWidget(self._update_pbtn, 2, 3)

        return layout

    def _on_update_clicked(self) -> None:
        isDown = self._update_pbtn.isChecked()
        if isDown:
            self._set_sbox.setEnabled(True)
            self._end_polling()
        else:
            self._set_new_set_point()
            self._set_sbox.setEnabled(False)
            self._begin_polling()

    def _begin_polling(self) -> None:
        """Initiate polling the TC4820 device."""
        # SerialDevicePanel.set_controls_enabled() will enable these, but
        # we want them to begin disabled
        self._set_sbox.setEnabled(False)
        if self._name.count("cold"):
            self._update_pbtn.setEnabled(False)
        self._poll_tc4820()
        self._poll_light.timer.start(self._poll_interval)

    def _end_polling(self) -> None:
        """Terminate polling the TC4820 device."""
        self._poll_light.timer.stop()

    def _poll_tc4820(self) -> None:
        """Polls the device to obtain the latest info."""
        self._poll_light.flash()
        pub.sendMessage(
            f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{self._name}_bb.request"
        )

    def _update_controls(self, properties: dict):
        """Update panel with latest info from temperature controller.

        Args:
            properties: dictionary containing the retrieved properties
        """
        self._control_val.setText(f"{properties['temperature']: .2f}")
        self._power_bar.setValue(properties["power"])
        self._power_label.setText(f"{properties['power']}")
        self._set_sbox.setValue(int(properties["set_point"]))
        if properties["alarm_status"] != 0:
            self._alarm_light._turn_on()
        elif self._alarm_light._is_on:
            self._alarm_light._turn_off()

    def _update_pt100(self, temperatures: list[Decimal], time: datetime):
        """Show the latest blackbody temperature.

        Args:
            temperatures: list of temperatures retrieved from device
            time: the timestamp at which the properties were sent
        """
        self._pt100_val.setText(f"{temperatures[self._temperature_idx]: .2f}")

    def _set_new_set_point(self) -> None:
        """Send new target temperature to temperature controller."""
        pub.sendMessage(
            f"serial.{TEMPERATURE_CONTROLLER_TOPIC}.{self._name}_bb.change_set_point",
            temperature=Decimal(self._set_sbox.value()),
        )


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()

    layout = QGridLayout()

    temperature_plot = TemperaturePlot()
    dp9800 = DP9800Controls()
    tc4820_hot = TC4820Controls("hot", TEMPERATURE_MONITOR_HOT_BB_IDX)
    tc4820_cold = TC4820Controls("cold", TEMPERATURE_MONITOR_COLD_BB_IDX)

    layout.addWidget(temperature_plot, 0, 0, 1, 0)
    layout.addWidget(dp9800, 1, 0, 1, 0)
    layout.addWidget(tc4820_hot, 2, 0)
    layout.addWidget(tc4820_cold, 2, 1)

    centralWidget = QWidget()
    centralWidget.setLayout(layout)

    window.setCentralWidget(centralWidget)
    window.show()
    app.exec()
