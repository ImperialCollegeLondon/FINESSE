"""Provides the base class for stepper motor implementations."""
from abc import ABC, abstractmethod
from typing import Union

from ..config import ANGLE_PRESETS


class StepperMotorBase(ABC):
    """A base class for stepper motor implementations."""

    @staticmethod
    def preset_angle(name: str) -> float:
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

    def home(self) -> None:
        """Return the stepper motor to its home position.

        This default implementation just uses the preset angle for home, but it may be a
        special operation for some devices.
        """
        self.move_to(self.preset_angle("home"))

    @abstractmethod
    def get_steps_per_rotation(self) -> int:
        """Get the number of steps that correspond to a full rotation."""

    @abstractmethod
    def move_to_step(self, step: int) -> None:
        """Move the stepper motor to the specified absolute position."""

    def move_to(self, target: Union[float, str]) -> None:
        """Move the motor to a specified rotation.

        Args:
            target: The target angle (in degrees) or the name of a preset
        """
        if isinstance(target, str):
            # Homing may be a special operation
            if target == "home":
                self.home()
                return

            target = self.preset_angle(target)

        if target < 0.0 or target > 270.0:
            raise ValueError("Angle must be between 0° and 270°")

        step = round(self.get_steps_per_rotation() * target / 360.0)
        self.move_to_step(step)
