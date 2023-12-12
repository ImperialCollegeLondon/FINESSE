"""Tests for DummyOPUSInterface."""

from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest
from statemachine import State

from finesse.hardware.plugins.spectrometer.dummy_opus_interface import (
    DummyOPUSInterface,
    OPUSError,
    OPUSErrorInfo,
    OPUSStateMachine,
)


@pytest.fixture
@patch("finesse.hardware.plugins.spectrometer.dummy_opus_interface.QTimer")
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

    with pytest.raises(OPUSError):
        dev.request_command("status")


_COMMANDS = (
    ("cancel", OPUSStateMachine.measuring, "stop"),
    ("stop", OPUSStateMachine.measuring, "stop"),
    ("start", OPUSStateMachine.connected, "start"),
    ("connect", OPUSStateMachine.idle, None),
)


@pytest.mark.parametrize("command,initial_state,timer_command", _COMMANDS)
def test_request_command_success(
    command: str,
    initial_state: State,
    timer_command: str | None,
    dev: DummyOPUSInterface,
) -> None:
    """Test the request_command() method."""
    with patch.object(dev.state_machine, "measure_timer") as timer_mock:
        with patch.object(dev, "send_response") as response_mock:
            dev.state_machine.current_state = initial_state
            dev.request_command(command)

    # Check that the right response message was sent
    state = dev.state_machine.current_state
    response_mock.assert_called_once_with(command, status=state.value, text=state.name)

    # Check that the right thing has been done to the timer
    if timer_command:
        getattr(timer_mock, timer_command).assert_called_once()


@pytest.mark.parametrize(
    "command,initial_state",
    (
        (command, state)
        for command, required_state, _ in _COMMANDS
        for state in OPUSStateMachine.states
        if state != required_state  # only choose invalid states
    ),
)
def test_request_command_fail(
    command: str, initial_state: State, dev: DummyOPUSInterface
) -> None:
    """Test the request_command() method when the initial state is wrong."""
    with pytest.raises(OPUSError):
        dev.state_machine.current_state = initial_state
        dev.request_command(command)


def test_request_command_bad_command(dev: DummyOPUSInterface) -> None:
    """Check that request_command() handles non-existent commands correctly."""
    with pytest.raises(OPUSError):
        dev.request_command("non_existent_command")
