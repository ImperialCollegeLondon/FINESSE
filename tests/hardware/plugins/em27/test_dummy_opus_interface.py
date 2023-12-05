"""Tests for DummyOPUSInterface."""

from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest
from statemachine import State

from finesse.hardware.plugins.em27.dummy_opus_interface import (
    DummyOPUSInterface,
    OPUSErrorInfo,
    OPUSStateMachine,
)


@pytest.fixture
@patch("finesse.hardware.plugins.em27.dummy_opus_interface.QTimer")
def dev(timer_mock: Mock) -> DummyOPUSInterface:
    """A fixture for DummyOPUSInterface."""
    timer_mock.return_value = MagicMock()

    return DummyOPUSInterface()


def test_init(dev: DummyOPUSInterface) -> None:
    """Test that the timer's signal is connected correctly."""
    assert dev.last_error == OPUSErrorInfo.NO_ERROR

    timeout = cast(MagicMock, dev.state_machine.measure_timer.timeout)
    timeout.connect.assert_called_once_with(dev.state_machine.stop)


def test_finish_measuring(dev: DummyOPUSInterface) -> None:
    """Check that the finish_measuring() slot works."""
    dev.state_machine.current_state = OPUSStateMachine.measuring
    dev.state_machine.stop()
    assert dev.last_error == OPUSErrorInfo.NO_ERROR


@pytest.mark.parametrize(
    "state",
    (state for state in OPUSStateMachine.states if state != OPUSStateMachine.idle),
)
def test_request_status(state: State, dev: DummyOPUSInterface) -> None:
    """Test the request_status() method."""
    dev.state_machine.current_state = state

    with patch.object(dev, "send_response") as response_mock:
        dev.request_command("status")
        response_mock.assert_called_once_with(
            "status", status=state.value, text=state.name
        )


def test_request_status_idle(dev: DummyOPUSInterface) -> None:
    """Test the request_status() method raises an error if device not connected."""
    dev.state_machine.current_state = OPUSStateMachine.idle

    with patch.object(dev, "error_occurred") as error_mock:
        dev.request_command("status")
        error_mock.assert_called_once()


_COMMANDS = (
    ("cancel", OPUSStateMachine.measuring, "stop"),
    ("stop", OPUSStateMachine.measuring, "stop"),
    ("start", OPUSStateMachine.connected, "start"),
    ("connect", OPUSStateMachine.idle, None),
)


@pytest.mark.parametrize(
    "command,required_state,timer_command,initial_state",
    (
        (
            *command,
            state,
        )
        for state in OPUSStateMachine.states
        for command in _COMMANDS
    ),
)
def test_request_command(
    command: str,
    required_state: State,
    timer_command: str | None,
    initial_state: State,
    dev: DummyOPUSInterface,
) -> None:
    """Test the request_command() method."""
    with patch.object(dev.state_machine, "measure_timer") as timer_mock:
        with patch.object(dev, "send_response") as response_mock:
            with patch.object(dev, "error_occurred") as error_mock:
                dev.state_machine.current_state = initial_state
                dev.request_command(command)

    if initial_state != required_state:
        # Check the error was broadcast
        error_mock.assert_called_once()
        response_mock.assert_not_called()
        return

    # Check that no error was thrown
    error_mock.assert_not_called()

    # Check that the right response message was sent
    state = dev.state_machine.current_state
    response_mock.assert_called_once_with(command, status=state.value, text=state.name)

    # Check that the right thing has been done to the timer
    if timer_command:
        getattr(timer_mock, timer_command).assert_called_once()


def test_request_command_bad_command(dev: DummyOPUSInterface) -> None:
    """Check that request_command() handles non-existent commands correctly."""
    with patch.object(dev, "error_occurred") as error_mock:
        dev.request_command("non_existent_command")
        error_mock.assert_called_once()
