"""Panel and widgets related to the control of spectrometers."""
from collections.abc import Sequence
from functools import partial

from frozendict import frozendict
from pubsub import pub
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from finesse.config import SPECTROMETER_TOPIC
from finesse.gui.device_panel import DevicePanel
from finesse.spectrometer_status import SpectrometerStatus


class SpectrometerControl(DevicePanel):
    """Class to monitor and control spectrometers."""

    _COMMANDS = ("connect", "start", "stop", "cancel")
    """The default commands shown."""

    _ENABLED_BUTTONS = frozendict(
        {
            SpectrometerStatus.IDLE: {"connect"},
            SpectrometerStatus.CONNECTED: {"start"},
            SpectrometerStatus.MEASURING: {"stop", "cancel"},
        }
    )
    """Which buttons to enable for different states."""

    def __init__(self, commands: Sequence[str] = _COMMANDS) -> None:
        """Create the widgets to monitor and control the spectrometer."""
        super().__init__(SPECTROMETER_TOPIC, "Spectrometer")

        self._buttons: dict[str, QPushButton] = {}
        """Buttons for the different spectrometer commands."""
        self._status_label = QLabel("Status:")
        """A label showing the current status of the device."""

        layout = QVBoxLayout()
        layout.addLayout(self._create_buttons(commands))
        layout.addWidget(self._status_label)
        self.setLayout(layout)

        pub.subscribe(self._on_status_changed, f"device.{SPECTROMETER_TOPIC}.status")

    def _create_buttons(self, commands: Sequence[str]) -> QHBoxLayout:
        """Creates the buttons.

        Returns:
            The layout with the buttons
        """
        btn_layout = QHBoxLayout()

        for name in commands:
            button = QPushButton(name.capitalize())
            button.setEnabled(False)
            button.clicked.connect(
                partial(self.on_command_button_clicked, command=name.lower())
            )
            btn_layout.addWidget(button)

            self._buttons[name] = button

        return btn_layout

    def _on_status_changed(self, status: SpectrometerStatus) -> None:
        """Update the GUI based on the status."""
        self._status_label.setText(f"Status: <b>{status.name}</b>")

        # Enable/disable buttons depending on the spectrometer's status
        to_enable = self._ENABLED_BUTTONS.get(status, set())
        for name, btn in self._buttons.items():
            btn.setEnabled(name in to_enable)

    def on_command_button_clicked(self, command: str) -> None:
        """Execute the given command by sending a message to the appropriate topic.

        Args:
            command: Command to be executed
        """
        pub.sendMessage(f"device.{SPECTROMETER_TOPIC}.request", command=command)
