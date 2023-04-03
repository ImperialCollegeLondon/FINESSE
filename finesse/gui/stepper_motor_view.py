"""Code for controlling the stepper motor which moves the mirror."""
from pubsub import pub
from PySide6.QtWidgets import QButtonGroup, QGridLayout, QPushButton, QSpinBox

from ..config import ANGLE_PRESETS, STEPPER_MOTOR_TOPIC
from .serial_device_panel import SerialDevicePanel


class StepperMotorControl(SerialDevicePanel):
    """A control showing buttons for moving the mirror to a target."""

    def __init__(self) -> None:
        """Create a new StepperMotorControl."""
        super().__init__(STEPPER_MOTOR_TOPIC, "Target control")

        layout = QGridLayout()

        # Bundle all the buttons for moving the mirror into one group
        self.button_group = QButtonGroup()
        self.button_group.buttonClicked.connect(self._preset_clicked)  # type: ignore

        # Add all the buttons for preset positions
        BUTTONS_PER_ROW = 4
        for i, preset in enumerate(ANGLE_PRESETS):
            btn = self._add_checkable_button(preset.upper())
            self.button_group.addButton(btn)

            row, col = divmod(i, BUTTONS_PER_ROW)
            layout.addWidget(btn, row, col)

        # We also have a way for users to move the mirror to an angle of their choice
        self.angle = QSpinBox()
        self.angle.setMaximum(359)
        self.goto = self._add_checkable_button("GOTO")

        layout.addWidget(self.angle, 1, 2)
        layout.addWidget(self.goto, 1, 3)

        self.setLayout(layout)

    def _add_checkable_button(self, name: str) -> QPushButton:
        """Add a selectable button to button_group."""
        btn = QPushButton(name)
        btn.setCheckable(True)

        self.button_group.addButton(btn)

        return btn

    def _preset_clicked(self, btn: QPushButton) -> None:
        """Move the stepper motor to preset position."""
        # If the motor is already moving, stop it now
        pub.sendMessage(f"serial.{STEPPER_MOTOR_TOPIC}.stop")

        target = float(self.angle.value()) if btn is self.goto else btn.text().lower()
        pub.sendMessage(f"serial.{STEPPER_MOTOR_TOPIC}.move.begin", target=target)
