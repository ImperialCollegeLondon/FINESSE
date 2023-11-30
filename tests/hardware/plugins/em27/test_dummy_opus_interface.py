"""Tests for DummyOPUSInterface."""

from itertools import product
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


@pytest.mark.parametrize("state,error", product(OPUSStateMachine.states, OPUSErrorInfo))
def test_request_status(
    state: State,
    error: OPUSErrorInfo,
    dev: DummyOPUSInterface,
    sendmsg_mock: MagicMock,
) -> None:
    """Test the request_status() method."""
    dev.last_error = error
    dev.state_machine.current_state = state

    dev.request_command("status")
    sendmsg_mock.assert_called_once_with(
        "opus.response.status",
        status=state.value,
        text=state.name,
        error=OPUSErrorInfo.NOT_CONNECTED.to_tuple()
        if state == OPUSStateMachine.idle
        else error.to_tuple(),
    )


_COMMANDS = (
    ("cancel", OPUSStateMachine.measuring, OPUSErrorInfo.NOT_RUNNING, "stop"),
    (
        "stop",
        OPUSStateMachine.measuring,
        OPUSErrorInfo.NOT_RUNNING_OR_FINISHING,
        "stop",
    ),
    ("start", OPUSStateMachine.connected, OPUSErrorInfo.NOT_CONNECTED, "start"),
    ("connect", OPUSStateMachine.idle, OPUSErrorInfo.NOT_IDLE, None),
)


@pytest.mark.parametrize(
    "command,required_state,error,timer_command,initial_state",
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
    error: OPUSErrorInfo,
    timer_command: str | None,
    initial_state: State,
    dev: DummyOPUSInterface,
    sendmsg_mock: MagicMock,
) -> None:
    """Test the request_command() method."""
    with patch.object(dev.state_machine, "measure_timer") as timer_mock:
        dev.state_machine.current_state = initial_state

        dev.request_command(command)

        if initial_state == required_state:
            # If we're in the required state, no error should occur
            assert dev.last_error == OPUSErrorInfo.NO_ERROR

            # Check that the right thing has been done to the timer
            if timer_command:
                getattr(timer_mock, timer_command).assert_called_once()
        else:
            assert dev.last_error == error

        # Check that the right response message was sent
        state = dev.state_machine.current_state
        sendmsg_mock.assert_called_once_with(
            f"opus.response.{command}",
            status=state.value,
            text=state.name,
            error=dev.last_error.to_tuple(),
        )


def test_request_command_bad_command(
    dev: DummyOPUSInterface, sendmsg_mock: MagicMock
) -> None:
    """Check that request_command() handles non-existent commands correctly."""
    dev.request_command("non_existent_command")

    state = dev.state_machine.current_state
    sendmsg_mock.assert_called_once_with(
        "opus.response.non_existent_command",
        status=state.value,
        text=state.name,
        error=OPUSErrorInfo.UNKNOWN_COMMAND.to_tuple(),
    )
