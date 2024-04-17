"""Tests for the FTSW500Interface class."""

from contextlib import nullcontext as does_not_raise
from itertools import chain
from socket import AF_INET, SOCK_STREAM
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest

from finesse.config import (
    DEFAULT_FTSW500_HOST,
    DEFAULT_FTSW500_POLLING_INTERVAL,
    DEFAULT_FTSW500_PORT,
    FTSW500_TIMEOUT,
)
from finesse.hardware.plugins.spectrometer.ftsw500_interface import (
    FTSW500Error,
    FTSW500Interface,
    _parse_response,
)
from finesse.spectrometer_status import SpectrometerStatus


@pytest.fixture
@patch.object(FTSW500Interface, "_update_status")
@patch.object(FTSW500Interface, "pubsub_errors")
@patch("finesse.hardware.plugins.spectrometer.ftsw500_interface.QTimer")
@patch("finesse.hardware.plugins.spectrometer.ftsw500_interface.socket")
def ftsw(socket_mock: Mock, timer_mock: Mock, decorator_mock: Mock, status_mock: Mock):
    """Fixture providing FTSW500 interface."""
    return FTSW500Interface()


@pytest.mark.parametrize(
    "response,ret,raises",
    chain(
        # Success responses
        (
            (response, ret, does_not_raise())
            for response, ret in (("ACK", ""), ("ACK&some message", "some message"))
        ),
        # Errors
        (
            (response, None, pytest.raises(err))
            for response, err in (
                ("", ValueError),
                ("HELLO", ValueError),
                ("NAK", FTSW500Error),
                ("NAK&message", FTSW500Error),
            )
        ),
    ),
)
def test_parse_response(response: str, ret, raises):
    """Test the _parse_response() function."""
    with raises:
        assert _parse_response(response) == ret


@patch("finesse.hardware.plugins.spectrometer.ftsw500_interface.pubsub_errors")
@patch.object(FTSW500Interface, "_update_status")
def test_init(status_mock: Mock, decorator_mock: Mock, qtbot) -> None:
    """Test FTSW500Interface's constructor."""
    decorator_mock.return_value = status_mock

    sock = MagicMock()  # socket
    with patch(
        "finesse.hardware.plugins.spectrometer.ftsw500_interface.socket",
        MagicMock(return_value=sock),
    ) as socket_ctor:
        dev = FTSW500Interface()

        # Check socket is created correctly and connection is attempted
        socket_ctor.assert_called_once_with(AF_INET, SOCK_STREAM)
        sock.settimeout.assert_called_once_with(FTSW500_TIMEOUT)
        sock.connect.assert_called_once_with(
            (DEFAULT_FTSW500_HOST, DEFAULT_FTSW500_PORT)
        )

        # Check that _update_status() is called to get initial status
        status_mock.assert_called_once_with()

        # Check that timer to poll status is configured correctly but not started
        assert dev._status_timer.interval() == int(
            DEFAULT_FTSW500_POLLING_INTERVAL * 1000
        )
        assert dev._status_timer.isSingleShot()
        decorator_mock.assert_called_with(status_mock)
        assert not dev._status_timer.isActive()

        # Check signal works
        status_mock.reset_mock()
        dev._status_timer.timeout.emit()
        status_mock.assert_called_once_with()


@pytest.mark.parametrize("fileno,socket_open", ((i, i != -1) for i in range(-1, 4)))
def test_close(fileno: int, socket_open: bool, ftsw: FTSW500Interface) -> None:
    """Test the close method."""
    # Set fileno (fileno == -1 indicates that socket is closed)
    assert isinstance(ftsw._socket, Mock)
    ftsw._socket.fileno.return_value = fileno

    # Attempt to close device
    ftsw.close()

    # Check timer was stopped
    assert isinstance(ftsw._status_timer, Mock)
    ftsw._status_timer.stop.assert_called_once_with()

    # Check that the socket's close() method was called, if appropriate
    if socket_open:
        ftsw._socket.close.assert_called_once_with()
    else:
        ftsw._socket.close.assert_not_called()


@patch("finesse.hardware.plugins.spectrometer.ftsw500_interface._parse_response")
def test_make_request_good(parse_mock: Mock, ftsw: FTSW500Interface) -> None:
    """Test the _make_request() method handles good responses correctly."""
    parse_mock.return_value = "PARSED ARGUMENT"
    sock = cast(Mock, ftsw._socket)
    RESPONSE = "madeUpResponse"

    # recv() returns bytes
    sock.recv.return_value = f"{RESPONSE}\n".encode()

    # Send command
    assert ftsw._make_request("madeUpCommand") == "PARSED ARGUMENT"

    # Check that it is converted to bytes and terminated with a newline
    sock.sendall.assert_called_once_with(b"madeUpCommand\n")

    # Check that correct string was parsed
    parse_mock.assert_called_once_with(RESPONSE)


@pytest.mark.parametrize("response", ("", "madeUpBadResponse"))
def test_make_request_bad(response: str, ftsw: FTSW500Interface) -> None:
    """Test the _make_request() method when no newline is received."""
    sock = cast(Mock, ftsw._socket)

    with pytest.raises(FTSW500Error):
        # recv() returns bytes
        sock.recv.return_value = response.encode()

        # Send command
        ftsw._make_request("madeUpCommand")


@pytest.mark.parametrize(
    "input,output",
    chain(
        # Valid statuses
        ((i, SpectrometerStatus(i)) for i in range(4)),
        # User should re-request status
        ((-1, None),),
    ),
)
def test_get_status_good(
    input: int, output: SpectrometerStatus | None, ftsw: FTSW500Interface
) -> None:
    """Test the _get_status() method for all valid values."""
    with patch.object(ftsw, "_make_request") as request_mock:
        request_mock.return_value = str(input)
        assert ftsw._get_status() == output


@pytest.mark.parametrize("input", ("-2", "4", "a string"))
def test_get_status_bad(input: str, ftsw: FTSW500Interface) -> None:
    """Test the _get_status() method for invalid values.

    This includes out-of-range integers as well as non-integers.
    """
    with patch.object(ftsw, "_make_request") as request_mock:
        request_mock.return_value = input
        with pytest.raises(FTSW500Error):
            ftsw._get_status()


VALID_STATUSES = map(SpectrometerStatus, range(4))
"""All possible statuses for the FTSW500."""


@pytest.mark.parametrize("new_status", VALID_STATUSES)
def test_update_status_changed(
    new_status: SpectrometerStatus, ftsw: FTSW500Interface
) -> None:
    """Test the _update_status() method for when the status changes."""
    assert ftsw._status == SpectrometerStatus.UNDEFINED
    with patch.object(ftsw, "_get_status", return_value=new_status):
        with patch.object(ftsw, "send_status_message") as send_status_mock:
            ftsw._update_status()

            # Check status was changed
            assert ftsw._status == new_status

            # Check send_status_message() called
            send_status_mock.assert_called_once_with(new_status)

            # Check timer was restarted
            assert isinstance(ftsw._status_timer, Mock)
            ftsw._status_timer.start.assert_called_once_with()


@pytest.mark.parametrize("new_status", VALID_STATUSES)
def test_update_status_not_changed(
    new_status: SpectrometerStatus, ftsw: FTSW500Interface
) -> None:
    """Test the _update_status() method for when the status is unchanged."""
    ftsw._status = new_status  # set the old status
    with patch.object(ftsw, "_get_status", return_value=new_status):
        with patch.object(ftsw, "send_status_message") as send_status_mock:
            ftsw._update_status()

            # Check status is unchanged
            assert ftsw._status == new_status

            # Check send_status_message() not called
            send_status_mock.assert_not_called()

            # Check timer was restarted
            assert isinstance(ftsw._status_timer, Mock)
            ftsw._status_timer.start.assert_called_once_with()


def test_update_status_try_again(ftsw: FTSW500Interface) -> None:
    """Test the _update_status() method when the intermediate status is received."""
    assert ftsw._status == SpectrometerStatus.UNDEFINED
    with patch.object(ftsw, "_get_status", return_value=None):
        with patch.object(ftsw, "send_status_message") as send_status_mock:
            ftsw._update_status()

            # Check status is unchanged
            assert ftsw._status == SpectrometerStatus.UNDEFINED

            # Check send_status_message() not called
            send_status_mock.assert_not_called()

            # Check timer was restarted
            assert isinstance(ftsw._status_timer, Mock)
            ftsw._status_timer.start.assert_called_once_with()


def test_request_command(ftsw: FTSW500Interface) -> None:
    """Test the request_command() method."""
    with patch.object(ftsw, "_make_request") as request_mock:
        with patch.object(ftsw, "_update_status") as status_mock:
            ftsw.request_command("madeUpCommand")
            request_mock.assert_called_once_with("madeUpCommand")
            status_mock.assert_called_once_with()
