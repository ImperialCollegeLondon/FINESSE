"""Code for controlling the stepper motor which moves the mirror."""
from PySide6.QtWidgets import QGridLayout, QGroupBox, QPushButton, QSpinBox


class StepperMotorControl(QGroupBox):
    """A control showing buttons for moving the mirror to a target."""

    def __init__(self) -> None:
        """Create a new StepperMotorControl."""
        super().__init__("Target control")

        layout = QGridLayout()
        zenith = QPushButton("ZENITH")
        nadir = QPushButton("NADIR")
        hot_bb = QPushButton("HOT_BB")
        cold_bb = QPushButton("COLD_BB")
        home = QPushButton("HOME")
        park = QPushButton("PARK")
        angle = QSpinBox()
        angle.setMaximum(359)
        goto = QPushButton("GOTO")

        layout.addWidget(zenith, 0, 0)
        layout.addWidget(nadir, 0, 1)
        layout.addWidget(hot_bb, 0, 2)
        layout.addWidget(cold_bb, 0, 3)
        layout.addWidget(home, 1, 0)
        layout.addWidget(park, 1, 1)
        layout.addWidget(angle, 1, 2)
        layout.addWidget(goto, 1, 3)

        self.setLayout(layout)
