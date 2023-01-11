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
        if steps_per_rotation < 1:
            raise ValueError("steps_per_rotation must be at least one")

        self.steps_per_rotation = steps_per_rotation
        self.current_step = 0

        pub.subscribe(self.move_to, "stepper.move")

    @staticmethod
    def get_preset_angle(name: str) -> float:
        """Get the angle for one of the preset positions.

        Args:
            name: Name of preset angle
        Returns:
            The angle in degrees
        """
        try:
            return ANGLE_PRESETS[name]
        except KeyError as e:
            raise ValueError(f"{name} is not a valid preset") from e

    def move_to(self, target: Union[float, str]) -> None:
        """Move the motor to a specified rotation.

        Args:
            target: The target angle (in degrees) or the name of a preset
        """
        if isinstance(target, str):
            target = DummyStepperMotor.get_preset_angle(target)

        if target < 0.0 or target > 270.0:
            raise ValueError("Angle must be between 0° and 270°")
        step = round(self.steps_per_rotation * target / 360.0)
        self.current_step = step

        logging.info(f"Moving stepper motor to step {self.current_step} (={target}°)")
