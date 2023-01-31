"""Provides the base class for stepper motor implementations."""
from abc import ABC, abstractmethod
from typing import Optional, Union

from pubsub import pub

from ..config import ANGLE_PRESETS


class StepperMotorBase(ABC):
    """A base class for stepper motor implementations."""

    def __init__(self) -> None:
        """Create a new StepperMotorBase.

        Subscribe to stepper.move messages.
        """
        pub.subscribe(self.move_to, "stepper.move.begin")
        pub.subscribe(self.stop_moving, "stepper.stop")

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

    @property
    @abstractmethod
    def steps_per_rotation(self) -> int:
        """The number of steps that correspond to a full rotation."""

    @property
    @abstractmethod
    def step(self) -> int:
        """The current state of the device's step counter."""

    @step.setter
    @abstractmethod
    def step(self, step: int) -> None:
        """Move the stepper motor to the specified absolute position.

        Args:
            step: Which step position to move to
        """

    @abstractmethod
    def stop_moving(self) -> None:
        """Immediately stop moving the motor."""

    @abstractmethod
    def wait_until_stopped_sync(self, timeout: Optional[float] = None) -> None:
        """Wait until the motor has stopped moving.

        Args:
            timeout: Time to wait for motor to finish moving (None == forever)
        """

    @abstractmethod
    def wait_until_stopped_async(self) -> None:
        """Wait until the motor has stopped moving and send a message when done.

        The message is stepper.move.end.
        """

    @property
    def angle(self) -> float:
        """The current angle of the motor in degrees."""
        return self.step * 360.0 / self.steps_per_rotation

    def move_to(self, target: Union[float, str]) -> None:
        """Move the motor to a specified rotation and send message when complete.

        Sends a stepper.move.end message when finished.

        Args:
            target: The target angle (in degrees) or the name of a preset
        """
        if isinstance(target, str):
            target = self.preset_angle(target)

        if target < 0.0 or target > 270.0:
            raise ValueError("Angle must be between 0° and 270°")

        self.step = round(self.steps_per_rotation * target / 360.0)

        # Send a message when the motor has stopped moving
        self.wait_until_stopped_async()
