"""Code for controlling the stepper motor which moves the mirror."""
from typing import Optional

from pubsub import pub
from PySide6.QtWidgets import QGridLayout, QGroupBox, QPushButton, QSpinBox

from ..config import ANGLE_PRESETS


class StepperMotorControl(QGroupBox):
    """A control showing buttons for moving the mirror to a target."""

    def __init__(self) -> None:
        """Create a new StepperMotorControl."""
        super().__init__("Target control")

        layout = QGridLayout()

        BUTTONS_PER_ROW = 4
        for i, preset in enumerate(ANGLE_PRESETS):
            btn = self._create_stepper_button(preset.upper())
            row, col = divmod(i, BUTTONS_PER_ROW)
            layout.addWidget(btn, row, col)

        self.angle = QSpinBox()
        self.angle.setMaximum(359)
        self.goto = QPushButton("GOTO")
        self.goto.clicked.connect(self._goto_clicked)  # type: ignore

        layout.addWidget(self.angle, 1, 2)
        layout.addWidget(self.goto, 1, 3)

        self.setLayout(layout)

        self.last_clicked: Optional[QPushButton] = None

    def _create_stepper_button(self, name: str) -> QPushButton:
        """Create a button to move the motor to a preset position.

        Args:
            name: The name of the preset (will be converted to lowercase)
        """
        btn = QPushButton(name)
        btn.clicked.connect(lambda: self._preset_clicked(btn))  # type: ignore
        return btn

    def _set_selected_button(self, btn: QPushButton) -> None:
        """Change the currently selected button, indicated by colour.

        Args:
            btn: The just-clicked button
        """
        if self.last_clicked:
            self.last_clicked.setStyleSheet("")
        btn.setStyleSheet("background-color: blue")
        self.last_clicked = btn

    def _preset_clicked(self, btn: QPushButton) -> None:
        """Move the stepper motor to preset position."""
        self._set_selected_button(btn)
        pub.sendMessage("stepper.move", target=btn.text().lower())

    def _goto_clicked(self) -> None:
        """Move stepper motor to specified position."""
        self._set_selected_button(self.goto)
        pub.sendMessage("stepper.move", target=float(self.angle.value()))
