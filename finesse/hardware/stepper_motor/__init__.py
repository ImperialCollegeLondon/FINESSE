"""Code for interfacing with stepper motors."""
from functools import partial

from ...config import STEPPER_MOTOR_TOPIC
from ..serial_manager import SerialManager
from .dummy import DummyStepperMotor
from .st10_controller import ST10Controller

_serial_manager: SerialManager


def create_stepper_motor_serial_manager() -> None:
    """Create a SerialManager for the stepper motor device."""
    global _serial_manager
    _serial_manager = SerialManager(
        STEPPER_MOTOR_TOPIC, ST10Controller, partial(DummyStepperMotor, 3600)
    )
