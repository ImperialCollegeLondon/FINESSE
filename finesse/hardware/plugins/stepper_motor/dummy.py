"""Code for a fake stepper motor device."""
import logging

from pubsub import pub
from PySide6.QtCore import QTimer

from finesse.config import STEPPER_MOTOR_TOPIC
from finesse.hardware.plugins.stepper_motor.stepper_motor_base import StepperMotorBase


class DummyStepperMotor(StepperMotorBase, description="Dummy stepper motor"):
    """A fake stepper motor device used for testing the GUI without the hardware.

    This class uses a simple timer to notify when the move is complete after a fixed
    amount of time. It is not sophisticated enough to handle multiple queued moves as
    the ST10 controller does.
    """

    def __init__(
        self, steps_per_rotation: int = 3600, move_duration: float = 0.0
    ) -> None:
        """Create a new DummyStepperMotor.

        Args:
            steps_per_rotation: Number of motor steps for an entire rotation (360°)
            move_duration: Amount of time taken for each move
        """
        if steps_per_rotation < 1:
            raise ValueError("steps_per_rotation must be at least one")

        self._move_end_timer = QTimer()
        self._move_end_timer.setSingleShot(True)
        self._move_end_timer.setInterval(round(move_duration * 1000))
        self._move_end_timer.timeout.connect(self._on_move_end)
        self._notify_requested = False

        self._steps_per_rotation = steps_per_rotation
        self._step = 0

        super().__init__()

    @property
    def steps_per_rotation(self) -> int:
        """The number of steps that correspond to a full rotation."""
        return self._steps_per_rotation

    @property
    def is_moving(self) -> bool:
        """Whether the motor is currently moving."""
        return self._move_end_timer.isActive()

    @property
    def step(self) -> int | None:
        """The number of steps that correspond to a full rotation.

        As this can only be requested when the motor is stationary, if the motor is
        moving then None will be returned.
        """
        if self.is_moving:
            return None

        return self._step

    @step.setter
    def step(self, step: int) -> None:
        """Move the stepper motor to the specified absolute position.

        Args:
            step: Which step position to move to
        """
        logging.info(f"Moving stepper motor to step {step}")
        self._step = step
        self._move_end_timer.start()

    def stop_moving(self) -> None:
        """Immediately stop moving the motor."""
        logging.info("Stopping motor")
        self._move_end_timer.stop()
        self._on_move_end()

    def wait_until_stopped(self, timeout: float | None = None) -> None:
        """Wait until the motor has stopped moving.

        For this dummy class, this is a no-op.

        Args:
            timeout: Time to wait for motor to finish moving (None == forever)
        """

    def notify_on_stopped(self) -> None:
        """Wait until the motor has stopped moving and send a message when done.

        The message is stepper.move.end.
        """
        self._notify_requested = True

    def _on_move_end(self) -> None:
        """Run when the timer signals that the move has finished."""
        logging.info("Move finished")
        if self._notify_requested:
            self._notify_requested = False
            pub.sendMessage(f"device.{STEPPER_MOTOR_TOPIC}.move.end")
