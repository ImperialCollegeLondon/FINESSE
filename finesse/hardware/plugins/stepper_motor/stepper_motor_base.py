"""Provides the base class for stepper motor implementations."""
from abc import abstractmethod

from pubsub import pub

from finesse.config import ANGLE_PRESETS, STEPPER_MOTOR_TOPIC
from finesse.device_info import DeviceInstanceRef
from finesse.hardware.device_base import DeviceBase
from finesse.hardware.plugins import register_device_base_type
from finesse.hardware.pubsub_decorators import pubsub_errors

error_wrap = pubsub_errors(
    f"device.error.{STEPPER_MOTOR_TOPIC}",
    instance=DeviceInstanceRef(STEPPER_MOTOR_TOPIC),
)
"""Broadcast exceptions via pubsub."""


@register_device_base_type(STEPPER_MOTOR_TOPIC, "Stepper motor")
class StepperMotorBase(DeviceBase):
    """A base class for stepper motor implementations."""

    def __init__(self) -> None:
        """Create a new StepperMotorBase.

        Subscribe to stepper motor pubsub messages.
        """
        super().__init__()

        # Versions of methods which catch and broadcast errors via pubsub
        self._move_to = error_wrap(self.move_to)
        self._stop_moving = error_wrap(self.stop_moving)
        self._notify_on_stopped = error_wrap(self.notify_on_stopped)

        pub.subscribe(
            self._move_to,
            f"device.{STEPPER_MOTOR_TOPIC}.move.begin",
        )
        pub.subscribe(self._stop_moving, f"device.{STEPPER_MOTOR_TOPIC}.stop")
        pub.subscribe(
            self._notify_on_stopped, f"device.{STEPPER_MOTOR_TOPIC}.notify_on_stopped"
        )

    @staticmethod
    def send_error_message(error: BaseException) -> None:
        """Send an error message when a device error has occurred."""
        pub.sendMessage(
            f"device.error.{STEPPER_MOTOR_TOPIC}",
            instance=DeviceInstanceRef(STEPPER_MOTOR_TOPIC),
            error=error,
        )

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
    def step(self) -> int | None:
        """The current state of the device's step counter.

        As this can only be requested when the motor is stationary, if the motor is
        moving then None will be returned.
        """

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
    def wait_until_stopped(self, timeout: float | None = None) -> None:
        """Wait until the motor has stopped moving.

        Args:
            timeout: Time to wait for motor to finish moving (None == forever)
        """

    @abstractmethod
    def notify_on_stopped(self) -> None:
        """Wait until the motor has stopped moving and send a message when done.

        The message is stepper.move.end.
        """

    @property
    @abstractmethod
    def is_moving(self) -> bool:
        """Whether the motor is currently moving."""

    @property
    def angle(self) -> float | None:
        """The current angle of the motor in degrees.

        As this can only be requested when the motor is stationary, if the motor is
        moving then None will be returned.

        Returns:
            The current angle or None if the stepper motor is moving
        """
        step = self.step
        if step is None:
            return None

        return step * 360.0 / self.steps_per_rotation

    def move_to(self, target: float | str) -> None:
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
