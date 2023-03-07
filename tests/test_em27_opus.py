"""Tests for the interface to the EM27's OPUS control program."""
from typing import Any, Optional
from unittest.mock import MagicMock, patch

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
        opus.request_command("status")
        request_mock.emit.assert_called_once_with("stat.htm", "opus.response.status")


def test_request_command(opus: OPUSInterface) -> None:
    """Test OPUSInterface's request_command() method."""
    with patch.object(opus, "submit_request") as request_mock:
        opus.request_command("hello")
        request_mock.emit.assert_called_once_with(
            "cmd.htm?opusrshello", "opus.response.hello"
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


def _format_td(name: str, value: Any) -> str:
    if value is None:
        return ""
    return f'<td id="{name}">{str(value)}</td>'


def _get_opus_html(
    status: Optional[int],
    text: Optional[str],
    errcode: Optional[int],
    errtext: Optional[str],
) -> str:
    return f"""
    <html>
        <body>
            <table>
                <tr>
                    {_format_td("STATUS", status)}
                    {_format_td("TEXT", text)}
                    {_format_td("ERRCODE", errcode)}
                    {_format_td("ERRTEXT", errtext)}
                </tr>
            </table>
        </body>
    </html>
    """


@pytest.mark.parametrize(
    "http_status_code,status,text,errcode,errtext",
    (
        (http_status, status, text, errcode, errtext)
        for http_status in (200, 403, 404)
        for status in (None, 0, 1)
        for text in (None, "", "status text")
        for errcode in (None, 0, 1)
        for errtext in (None, "", "error text")
    ),
)
def test_parsing(
    http_status_code: int,
    status: Optional[int],
    text: Optional[str],
    errcode: Optional[int],
    errtext: Optional[str],
    opus: OPUSInterface,
    sendmsg_mock: MagicMock,
) -> None:
    """Test the OPUS parser."""
    html = _get_opus_html(status, text, errcode, errtext)

    # Mock a requests.Response
    response = MagicMock()
    response.status_code = http_status_code
    response.url = "https://example.com"
    response.content = html.encode()

    with patch.object(opus, "error_occurred") as error_mock:
        opus._parse_response(response, "my.topic")
        if http_status_code == 200:
            if status is None or text is None:
                # Required fields missing
                error_mock.assert_called()
            else:
                error = None if errcode is None else (errcode, errtext)
                sendmsg_mock.assert_called_once_with(
                    "my.topic", url=response.url, status=status, text=text, error=error
                )
                error_mock.assert_not_called()
        else:
            sendmsg_mock.assert_not_called()
            error_mock.assert_called_once()
