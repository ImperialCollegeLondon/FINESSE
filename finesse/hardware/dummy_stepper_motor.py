"""Code for a fake stepper motor device."""
import logging

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

        self.steps_per_rotation = steps_per_rotation
        self.current_step = 0

        pub.subscribe(self.move_to, "stepper.move")

    def get_steps_per_rotation(self) -> int:
        """Get the number of steps that correspond to a full rotation."""
        return self.steps_per_rotation

    def move_to_step(self, step: int) -> None:
        """Move the stepper motor to the specified absolute position."""
        self.current_step = step
        logging.info(f"Moving stepper motor to step {step}")
