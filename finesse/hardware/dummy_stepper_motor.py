"""Code for a fake stepper motor device."""
import logging
from typing import Union

from pubsub import pub

from ..config import ANGLE_PRESETS


class DummyStepperMotor:
    """A fake stepper motor device used for unit tests etc."""

    def __init__(self, steps_per_rotation: int) -> None:
        """Create a new DummyStepperMotor.

        Args:
            steps_per_rotation: Number of motor steps for an entire rotation (360°)
        """
        if steps_per_rotation < len(ANGLE_PRESETS):
            raise ValueError(f"steps_per_rotation must be >={len(ANGLE_PRESETS)}")

        self.steps_per_rotation = steps_per_rotation
        self.current_step = 0

        pub.subscribe(self.move_to, "stepper.move")

    @staticmethod
    def get_preset_step(name: str) -> int:
        """Get the angle for one of the preset positions.

        Args:
            name: Name of preset angle
        Returns:
            The step number (as int)
        """
        return ANGLE_PRESETS.index(name)

    def move_to(self, target: Union[float, str]) -> None:
        """Move the motor to a specified rotation.

        Args:
            target: The target angle (in degrees) or the name of a preset
        """
        if isinstance(target, str):
            self.current_step = DummyStepperMotor.get_preset_step(target)
            target_angle = self.current_step * 360 / self.steps_per_rotation
        else:
            step = round(self.steps_per_rotation * target / 360.0)
            if step < 0 or step >= self.steps_per_rotation:
                raise ValueError("step number is out of range")
            self.current_step = step
            target_angle = target

        logging.info(
            f"Moving stepper motor to step {self.current_step} (={target_angle}°)"
        )
