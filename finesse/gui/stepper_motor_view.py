"""Code for controlling the stepper motor which moves the mirror."""
from typing import Optional

from pubsub import pub
from PySide6.QtWidgets import QGridLayout, QGroupBox, QPushButton, QSpinBox


class StepperMotorControl(QGroupBox):
    """A control showing buttons for moving the mirror to a target."""

    def __init__(self) -> None:
        """Create a new StepperMotorControl."""
        super().__init__("Target control")

        layout = QGridLayout()
        zenith = self._create_stepper_button("ZENITH")
        nadir = self._create_stepper_button("NADIR")
        hot_bb = self._create_stepper_button("HOT_BB")
        cold_bb = self._create_stepper_button("COLD_BB")
        home = self._create_stepper_button("HOME")
        self.angle = QSpinBox()
        self.angle.setMaximum(359)
        self.goto = QPushButton("GOTO")
        self.goto.clicked.connect(self._goto_clicked)  # type: ignore

        self.last_clicked: Optional[QPushButton] = None

        layout.addWidget(zenith, 0, 0)
        layout.addWidget(nadir, 0, 1)
        layout.addWidget(hot_bb, 0, 2)
        layout.addWidget(cold_bb, 0, 3)
        layout.addWidget(home, 1, 0)
        layout.addWidget(self.angle, 1, 2)
        layout.addWidget(self.goto, 1, 3)

        self.setLayout(layout)

    def _create_stepper_button(self, name: str) -> QPushButton:
        btn = QPushButton(name)
        btn.clicked.connect(lambda: self._preset_clicked(btn))  # type: ignore
        return btn

    def _set_last_clicked(self, btn: QPushButton) -> None:
        if self.last_clicked:
            self.last_clicked.setStyleSheet("")
        btn.setStyleSheet("background-color: blue")
        self.last_clicked = btn

    def _preset_clicked(self, btn: QPushButton) -> None:
        self._set_last_clicked(btn)
        pub.sendMessage("stepper.move", step=btn.text().lower())

    def _goto_clicked(self) -> None:
        """Move stepper motor to specified position."""
        self._set_last_clicked(self.goto)
        pub.sendMessage("stepper.move", step=self.angle.value())
