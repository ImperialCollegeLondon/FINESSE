"""Code for interfacing with stepper motors."""
from functools import partial
from typing import cast

from finesse.config import STEPPER_MOTOR_TOPIC
from finesse.hardware.serial_manager import SerialManager, make_device_factory

from .dummy import DummyStepperMotor
from .st10_controller import ST10Controller
from .stepper_motor_base import StepperMotorBase

_serial_manager: SerialManager


def create_stepper_motor_serial_manager() -> None:
    """Create a SerialManager for the stepper motor device."""
    global _serial_manager
    _serial_manager = SerialManager(
        STEPPER_MOTOR_TOPIC,
        make_device_factory(
            ST10Controller,
            partial(DummyStepperMotor, steps_per_rotation=3600, move_duration=1.0),
        ),
    )


def get_stepper_motor_instance() -> StepperMotorBase | None:
    """Get the global instance of the stepper motor object."""
    global _serial_manager
    if not _serial_manager.is_open:
        return None
    return cast(StepperMotorBase, _serial_manager.device)
