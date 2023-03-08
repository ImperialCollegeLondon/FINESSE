"""Tests for DummyOPUSInterface."""

from itertools import product
from typing import Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from pubsub import pub
from statemachine import State

from finesse.hardware.dummy_opus import DummyOPUSInterface, OPUSError, OPUSStateMachine


@pytest.fixture
@patch("finesse.hardware.dummy_opus.QTimer")
def dev(timer_mock: Mock) -> DummyOPUSInterface:
    """A fixture for DummyOPUSInterface."""
    timer_mock.return_value = MagicMock()

    return DummyOPUSInterface()


@pytest.fixture()
def send_message_mock(monkeypatch) -> MagicMock:
    """Magic Mock patched over pubsub.pub.sendMessage."""
    mock = MagicMock()
    monkeypatch.setattr(pub, "sendMessage", mock)
    return mock


def test_init(dev: DummyOPUSInterface) -> None:
    """Test that the timer's signal is connected correctly."""
    assert dev.last_error == OPUSError.NO_ERROR

    timeout = dev.state_machine.measure_timer.timeout  # type: ignore
    timeout.connect.assert_called_once_with(dev.state_machine.stop)


def test_finish_measuring(dev: DummyOPUSInterface) -> None:
    """Check that the finish_measuring() slot works."""
    dev.state_machine.current_state = OPUSStateMachine.measuring
    dev.state_machine.stop()
    assert dev.last_error == OPUSError.NO_ERROR


@pytest.mark.parametrize("state,error", product(OPUSStateMachine.states, OPUSError))
def test_request_status(
    state: State,
    error: OPUSError,
    dev: DummyOPUSInterface,
    send_message_mock: MagicMock,
) -> None:
    """Test the request_status() method."""
    dev.last_error = error
    dev.state_machine.current_state = state

    dev.request_status()
    send_message_mock.assert_called_once_with(
        "opus.status.response",
        url="https://example.com",
        status=state.value,
        text=state.name,
        error=OPUSError.NOT_CONNECTED.to_tuple()
        if state == OPUSStateMachine.idle
        else error.to_tuple(),
    )


_COMMANDS = (
    ("cancel", OPUSStateMachine.measuring, OPUSError.NOT_RUNNING, "stop"),
    ("stop", OPUSStateMachine.measuring, OPUSError.NOT_RUNNING_OR_FINISHING, "stop"),
    ("start", OPUSStateMachine.connected, OPUSError.NOT_CONNECTED, "start"),
    ("connect", OPUSStateMachine.idle, OPUSError.NOT_IDLE, None),
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
    error: OPUSError,
    timer_command: Optional[str],
    initial_state: State,
    dev: DummyOPUSInterface,
    send_message_mock: MagicMock,
) -> None:
    """Test the request_command() method."""
    with patch.object(dev.state_machine, "measure_timer") as timer_mock:
        dev.state_machine.current_state = initial_state

        dev.request_command(command)

        if initial_state == required_state:
            # If we're in the required state, no error should occur
            assert dev.last_error == OPUSError.NO_ERROR

            # Check that the right thing has been done to the timer
            if timer_command:
                getattr(timer_mock, timer_command).assert_called_once()
        else:
            assert dev.last_error == error

        # Check that the right response message was sent
        state = dev.state_machine.current_state
        send_message_mock.assert_called_once_with(
            "opus.command.response",
            url="https://example.com",
            status=state.value,
            text=state.name,
            error=dev.last_error.to_tuple(),
        )


def test_request_command_bad_command(
    dev: DummyOPUSInterface, send_message_mock: MagicMock
) -> None:
    """Check that request_command() handles non-existent commands correctly."""
    dev.request_command("non_existent_command")

    state = dev.state_machine.current_state
    send_message_mock.assert_called_once_with(
        "opus.command.response",
        url="https://example.com",
        status=state.value,
        text=state.name,
        error=OPUSError.UNKNOWN_COMMAND.to_tuple(),
    )
