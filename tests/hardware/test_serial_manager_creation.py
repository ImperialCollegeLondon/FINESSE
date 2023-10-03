"""Test that SerialManagers for the different devices are set up correctly."""
from unittest.mock import MagicMock, Mock, patch

from finesse.config import DUMMY_DEVICE_PORT, STEPPER_MOTOR_TOPIC


@patch("finesse.hardware.plugins.stepper_motor.DummyStepperMotor")
@patch("finesse.hardware.plugins.stepper_motor.ST10Controller")
@patch("finesse.hardware.serial_manager.Serial")
def test_stepper_motor(
    serial_mock: Mock, st10_mock: Mock, dummy_mock: Mock, subscribe_mock: Mock
) -> None:
    """Test for the stepper motor SerialManager."""
    from finesse.hardware.plugins.stepper_motor import (
        create_stepper_motor_serial_manager,
    )

    create_stepper_motor_serial_manager()
    from finesse.hardware.plugins.stepper_motor import _serial_manager

    assert _serial_manager.name == STEPPER_MOTOR_TOPIC

    # Check the dummy device is created
    _serial_manager._open(DUMMY_DEVICE_PORT, 1234)
    dummy_mock.assert_called_once()

    # Check the real device is created
    serial = MagicMock()
    serial_mock.return_value = serial
    _serial_manager._open("COM1", 1234)
    serial_mock.assert_called_once_with("COM1", 1234)
    st10_mock.assert_called_once_with(serial)


@patch("finesse.hardware.plugins.temperature.DummyTemperatureController")
@patch("finesse.hardware.plugins.temperature.TC4820")
@patch("finesse.hardware.serial_manager.Serial")
def test_tc4820(
    serial_mock: Mock, tc4820_mock: Mock, dummy_mock: Mock, subscribe_mock: Mock
) -> None:
    """Test for the two TC4820 SerialManagers."""
    serial = MagicMock()
    serial_mock.return_value = serial

    from finesse.hardware.plugins.temperature import (
        create_temperature_controller_serial_managers,
    )

    create_temperature_controller_serial_managers()
    from finesse.hardware.plugins.temperature import (
        _serial_manager_cold_bb,
        _serial_manager_hot_bb,
    )

    # Check the dummy devices are created
    _serial_manager_cold_bb._open(DUMMY_DEVICE_PORT, 1234)
    dummy_mock.assert_called_once()
    dummy_mock.reset_mock()
    _serial_manager_hot_bb._open(DUMMY_DEVICE_PORT, 1234)
    dummy_mock.assert_called_once()

    # Check the real devices are created
    _serial_manager_cold_bb._open("COM1", 1234)
    tc4820_mock.assert_called_once()
    tc4820_mock.reset_mock()
    _serial_manager_hot_bb._open("COM1", 1234)
    tc4820_mock.assert_called_once()
