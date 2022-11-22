"""Code for a fake stepper motor device."""
import logging

from pubsub import pub


class DummyStepperMotor:
    """A fake stepper motor device used for unit tests etc."""

    def __init__(self, steps_per_rotation: int) -> None:
        """Create a new DummyStepperMotor.

        Args:
            steps_per_rotation: Number of motor steps for an entire rotation (360°)
        """
        if steps_per_rotation <= 0:
            raise ValueError("steps_per_rotation must be >0")

        self.max_steps = steps_per_rotation - 1
        self.current_step = 0

        pub.subscribe(self.move_to, "stepper.move")

    def move_to(self, step_number: int) -> None:
        """Move the motor to a specified rotation.

        Args:
            step_number: The target step number
        """
        if step_number < 0 or step_number > self.max_steps:
            raise ValueError("step_number is out of range")

        self.current_step = step_number

        logging.info(f"Moving stepper motor to {step_number}")
