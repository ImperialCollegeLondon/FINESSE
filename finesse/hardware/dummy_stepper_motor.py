"""Code for a fake stepper motor device."""
import logging
from typing import Union

from pubsub import pub

_PRESETS = ("zenith", "nadir", "hot_bb", "cold_bb", "home")


class DummyStepperMotor:
    """A fake stepper motor device used for unit tests etc."""

    def __init__(self, steps_per_rotation: int) -> None:
        """Create a new DummyStepperMotor.

        Args:
            steps_per_rotation: Number of motor steps for an entire rotation (360°)
        """
        if steps_per_rotation < len(_PRESETS):
            raise ValueError(f"steps_per_rotation must be >={len(_PRESETS)}")

        self.max_steps = steps_per_rotation - 1
        self.current_step = 0

        pub.subscribe(self.move_to, "stepper.move")

    @staticmethod
    def get_preset_angle(name: str) -> int:
        """Get the angle for one of the preset positions.

        Args:
            name: Name of preset angle
        """
        return _PRESETS.index(name)

    def move_to(self, step: Union[int, str]) -> None:
        """Move the motor to a specified rotation.

        Args:
            step: The target step number or the name of a preset
        """
        if isinstance(step, str):
            step = DummyStepperMotor.get_preset_angle(step)

        if step < 0 or step > self.max_steps:
            raise ValueError("step_number is out of range")

        self.current_step = step

        logging.info(f"Moving stepper motor to {step}")
