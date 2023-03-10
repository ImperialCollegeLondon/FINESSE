"""Code for a fake stepper motor device."""
import logging
from typing import Optional

from pubsub import pub

from .stepper_motor_base import StepperMotorBase


class DummyStepperMotor(StepperMotorBase):
    """A fake stepper motor device used for unit tests etc."""

    def __init__(self, steps_per_rotation: int) -> None:
        """Create a new DummyStepperMotor.

        Args:
            steps_per_rotation: Number of motor steps for an entire rotation (360°)
        """
        if steps_per_rotation < 1:
            raise ValueError("steps_per_rotation must be at least one")

        self._steps_per_rotation = steps_per_rotation
        self._step = 0

        super().__init__()

    def close(self) -> None:
        """Shut down the device."""

    @property
    def steps_per_rotation(self) -> int:
        """The number of steps that correspond to a full rotation."""
        return self._steps_per_rotation

    @property
    def step(self) -> int:
        """The number of steps that correspond to a full rotation."""
        return self._step

    @step.setter
    def step(self, step: int) -> None:
        """Move the stepper motor to the specified absolute position.

        Args:
            step: Which step position to move to
        """
        self._step = step
        logging.info(f"Moving stepper motor to step {step}")

    def stop_moving(self) -> None:
        """Immediately stop moving the motor."""
        logging.info("Stopping motor")

    def wait_until_stopped(self, timeout: Optional[float] = None) -> None:
        """Wait until the motor has stopped moving.

        For this dummy class, this is a no-op.

        Args:
            timeout: Time to wait for motor to finish moving (None == forever)
        """

    def notify_on_stopped(self) -> None:
        """Wait until the motor has stopped moving and send a message when done.

        The message is stepper.move.end.

        As this is a dummy class, this completes immediately.
        """
        pub.sendMessage("stepper.move.end")
