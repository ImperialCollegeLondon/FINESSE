"""Panel and widgets related to temperature monitoring."""
from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import Tuple

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from pubsub import pub
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QWidget,
)

from .led_icons import LEDIcon


def get_temperature_data() -> Tuple[float, float, float]:
    """Read temperatures of hot and cold blackbodies.

    Returns:
        time: The time at which the temperatures were read
        hot_bb_temp: The temperature of the hot blackbody
        cold_bb_temp: The temperature of the cold blackbody
    """
    time_now = datetime.now().timestamp()

    # Placeholder. Later read from sensors.
    hot_bb_temp = (60 * time_now + 50) % 70
    cold_bb_temp = (5 * time_now + 1) % 8
    return (time_now, hot_bb_temp, cold_bb_temp)


class BBMonitor(QGroupBox):
    """Widgets to view the temperature properties."""

    def __init__(self) -> None:
        """Creates a panel with a graph to monitor the blackbody temperatures."""
        super().__init__("BB Monitor")

        layout = self._create_controls()
        self.setLayout(layout)

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

        layout.addWidget(self._btns["hot"], 0, 0)
        layout.addWidget(self._btns["cold"], 1, 0)
        layout.addWidget(self._canvas, 0, 1, 2, 1)

        return layout

    def _create_figure(self) -> None:
        """Creates the matplotlib figure to be contained within the panel."""
        self._figure, ax = plt.subplots()
        self._ax = {"hot": ax}
        self._canvas = FigureCanvasQTAgg(self._figure)

        # Placeholder callback to test updating of figure
        self._canvas.mpl_connect("button_press_event", self._update_figure)

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
        """Shows or hides BB plots."""
        state = self._ax[name].yaxis.get_visible()
        self._btns[name].setFlat(state)
        self._ax[name].yaxis.set_visible(not state)
        self._ax[name].lines[0].set_visible(not state)
        self._canvas.draw()

    def _update_figure(self, event) -> None:
        """Updates the matplotlib figure to be contained within the panel."""
        time = list(self._ax["hot"].lines[0].get_xdata())
        hot_data = list(self._ax["hot"].lines[0].get_ydata())
        cold_data = list(self._ax["cold"].lines[0].get_ydata())

        time.pop(0)
        hot_data.pop(0)
        cold_data.pop(0)

        new_time, new_hot_data, new_cold_data = get_temperature_data()
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


class DP9800(QGroupBox):
    """Widgets to view the DP9800 properties."""

    def __init__(self, num_channels: int) -> None:
        """Creates the widgets to monitor DP9800.

        Args:
            num_channels (int): Number of Pt 100 channels being monitored
        """
        super().__init__("DP9800")

        self._num_channels = num_channels

        layout = self._create_controls()
        self.setLayout(layout)

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
            channel_tbox.setReadOnly(True)
            self._channels.append(channel_tbox)
            layout.addWidget(channel_tbox, 1, i + 1)

        poll_label = QLabel("POLL")
        poll_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(poll_label, 0, 9, 2, 1)

        self._poll_light = LEDIcon.create_poll_icon()
        layout.addWidget(self._poll_light, 0, 10, 2, 1)

        return layout


class TC4820(QGroupBox):
    """Widgets to view the TC4820 properties."""

    def __init__(self, name: str) -> None:
        """Creates the widgets to control and monitor a TC4820.

        Args:
            name (str): Name of the blackbody the TC4820 is controlling
        """
        super().__init__(f"TC4820 {name.upper()}")
        self._name = name

        layout = self._create_controls()
        self.setLayout(layout)

        self._begin_polling()

        pub.subscribe(self._begin_polling, f"temperature_controller.{name}.open")
        pub.subscribe(self._end_polling, f"temperature_controller.{name}.close")
        pub.subscribe(self._update_controls, f"temperature_controller.{name}.response")
        pub.subscribe(self._update_pt100, "dp9800.data.response")

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
        self._poll_light._timer.timeout.connect(self._poll_tc4820)  # type: ignore
        self._alarm_light = LEDIcon.create_alarm_icon()
        layout.addWidget(self._poll_light, 0, 5)
        layout.addWidget(self._alarm_light, 2, 5)

        self._set_sbox = QSpinBox()
        layout.addWidget(self._set_sbox, 2, 1)

        self._update_pbtn = QPushButton("UPDATE")
        self._update_pbtn.clicked.connect(self._set_new_set_point)  # type: ignore
        layout.addWidget(self._update_pbtn, 2, 3)

        return layout

    def _begin_polling(self) -> None:
        """Initiate polling the TC4820 device."""
        self._poll_light._timer.start(2000)

    def _end_polling(self) -> None:
        """Terminate polling the TC4820 device."""
        self._poll_light._timer.stop()

    def _poll_tc4820(self) -> None:
        """Polls the device to obtain the latest info."""
        self._poll_light._flash()
        pub.sendMessage(f"temperature_controller.{self._name}.request")

    def _update_controls(self, properties: dict):
        """Update panel with latest info from temperature controller."""
        self._control_val.setText(f"{properties['temperature']: .2f}")
        self._power_bar.setValue(properties["power"])
        self._power_label.setText(f"{properties['power']}")
        self._set_sbox.setValue(int(properties["set_point"]))
        if properties["alarm_status"] != 0:
            self._alarm_light._turn_on()
        else:
            if self._alarm_light._is_on:
                self._alarm_light._turn_off()

    def _update_pt100(self, values: list[Decimal], time: float):
        """Show the latest blackbody temperature."""
        if self._name.count("hot"):
            self._pt100_val.setText(f"{values[6]: .2f}")
        elif self._name.count("cold"):
            self._pt100_val.setText(f"{values[7]: .2f}")

    def _set_new_set_point(self) -> None:
        """Send new target temperature to temperature controller."""
        pub.sendMessage(
            f"temperature_controller.{self._name}.change_set_point",
            temperature=Decimal(self._set_sbox.value()),
        )


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()

    layout = QGridLayout()

    bb_monitor = BBMonitor()
    dp9800 = DP9800(8)
    tc4820_hot = TC4820("hot")
    tc4820_cold = TC4820("cold")

    layout.addWidget(bb_monitor, 0, 0, 1, 0)
    layout.addWidget(dp9800, 1, 0, 1, 0)
    layout.addWidget(tc4820_hot, 2, 0)
    layout.addWidget(tc4820_cold, 2, 1)

    centralWidget = QWidget()
    centralWidget.setLayout(layout)

    window.setCentralWidget(centralWidget)
    window.show()
    app.exec()
