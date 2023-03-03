"""Tests for the interface to the EM27's OPUS control program."""
from unittest.mock import patch

import pytest

from finesse.config import OPUS_IP
from finesse.hardware.em27_opus import OPUSInterface, OPUSRequester


@pytest.fixture
@patch("finesse.hardware.em27_opus.QThread.start")
def opus(mock) -> OPUSInterface:
    """Fixture for OPUSInterface."""
    return OPUSInterface()


def test_request_status(opus: OPUSInterface) -> None:
    """Test OPUSInterface's request_status() method."""
    with patch.object(opus, "submit_request") as request_mock:
        opus.request_status()
        request_mock.emit.assert_called_once_with("stat.htm", "opus.response.status")


def test_request_command(opus: OPUSInterface) -> None:
    """Test OPUSInterface's request_command() method."""
    with patch.object(opus, "submit_request") as request_mock:
        opus.request_command("hello")
        request_mock.emit.assert_called_once_with(
            "cmd.htm?opusrshello", "opus.response.command"
        )


@patch("finesse.hardware.em27_opus.requests")
def test_make_request_success(requests_mock) -> None:
    """Test OPUSRequester's make_request() method with a successful request."""
    requester = OPUSRequester(5.0)

    with patch.object(requester, "request_complete") as request_complete_mock:
        filename = "filename"
        topic = "topic"
        requests_mock.get.return_value = "MAGIC"
        requester.make_request(filename, topic)
        requests_mock.get.assert_called_once_with(
            f"http://{OPUS_IP}/opusrs/{filename}", timeout=5.0
        )

        request_complete_mock.emit.assert_called_once_with("MAGIC", topic)


@patch("finesse.hardware.em27_opus.requests")
def test_make_request_error(requests_mock) -> None:
    """Test OPUSRequester's make_request() method with failed request."""
    requester = OPUSRequester(5.0)
    error = RuntimeError("Request failed")
    requests_mock.get.side_effect = error

    with patch.object(requester, "request_error") as request_error_mock:
        filename = "filename"
        topic = "topic"
        requests_mock.get.return_value = "MAGIC"
        requester.make_request(filename, topic)
        requests_mock.get.assert_called_once_with(
            f"http://{OPUS_IP}/opusrs/{filename}", timeout=5.0
        )

        request_error_mock.emit.assert_called_once_with(error)
