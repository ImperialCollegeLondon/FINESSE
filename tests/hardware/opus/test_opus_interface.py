"""Tests for the interface to the EM27's OPUS control program."""
from itertools import product
from typing import Any, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtNetwork import QNetworkReply

from finesse.config import OPUS_IP
from finesse.em27_status import EM27Status
from finesse.hardware.opus.em27 import OPUSError, OPUSInterface, parse_response


@pytest.fixture
def opus(qtbot) -> OPUSInterface:
    """Fixture for OPUSInterface."""
    return OPUSInterface()


@patch("finesse.hardware.opus.em27.QNetworkRequest")
def test_request_status(network_request_mock: Mock, opus: OPUSInterface, qtbot) -> None:
    """Test OPUSInterface's request_status() method."""
    with patch.object(opus, "_manager"):
        opus.request_command("status")
        network_request_mock.assert_called_once_with(
            f"http://{OPUS_IP}/opusrs/stat.htm"
        )


@patch("finesse.hardware.opus.em27.QNetworkRequest")
def test_request_command(
    network_request_mock: Mock, opus: OPUSInterface, qtbot
) -> None:
    """Test OPUSInterface's request_command() method."""
    request = MagicMock()
    network_request_mock.return_value = request
    reply = MagicMock()

    with patch.object(opus, "_manager") as manager_mock:
        with patch.object(opus, "_on_reply_received") as reply_received_mock:
            manager_mock.get.return_value = reply
            opus.request_command("hello")
            network_request_mock.assert_called_once_with(
                f"http://{OPUS_IP}/opusrs/cmd.htm?opusrshello"
            )
            request.setTransferTimeout.assert_called_once_with(
                round(1000 * opus._timeout)
            )

            # Check that the reply will be handled by _on_reply_received()
            connect_mock = reply.finished.connect
            connect_mock.assert_called_once()
            handler = connect_mock.call_args_list[0].args[0]
            handler()
            reply_received_mock.assert_called_once()


def _format_td(name: str, value: Any) -> str:
    if value is None:
        return ""
    return f'<td id="{name}">{str(value)}</td>'


def _get_opus_html(
    status: Optional[int],
    text: Optional[str],
    errcode: Optional[int] = None,
    errtext: Optional[str] = None,
    extra_text: str = "",
) -> str:
    return f"""
    <html>
        <body>
            <table>
                <tr>
                    {extra_text}
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
    "status,text",
    product((EM27Status.IDLE, EM27Status.CONNECTING), ("", "status text")),
)
def test_parse_response_no_error(status: EM27Status, text: str) -> None:
    """Test parse_response() works when no error has occurred."""
    response = _get_opus_html(status.value, text)
    parsed_status, parsed_text, parsed_error = parse_response(response)
    assert parsed_status == status
    assert parsed_text == text
    assert parsed_error is None


@pytest.mark.parametrize("errcode,errtext", product(range(2), ("", "error text")))
def test_parse_response_error(errcode: int, errtext: str) -> None:
    """Test parse_response() works when an error has occurred."""
    response = _get_opus_html(
        EM27Status.CONNECTING.value, "status text", errcode, errtext
    )
    parsed_status, parsed_text, parsed_error = parse_response(response)
    assert parsed_status == EM27Status.CONNECTING
    assert parsed_text == "status text"
    assert parsed_error == (errcode, errtext)


@pytest.mark.parametrize("status,text", ((None, "text"), (1, None), (None, None)))
def test_parse_response_missing_fields(
    status: Optional[int], text: Optional[str]
) -> None:
    """Test parse_response() raises an error if fields are missing."""
    response = _get_opus_html(status, text)
    with pytest.raises(OPUSError):
        parse_response(response)


def test_parse_response_no_id(opus: OPUSInterface) -> None:
    """Test that parse_response() can handle <td> tags without an id."""
    response = _get_opus_html(
        EM27Status.CONNECTING.value, "text", 1, "errtext", "<td>something</td>"
    )
    parsed_status, parsed_text, parsed_error = parse_response(response)
    assert parsed_status == EM27Status.CONNECTING
    assert parsed_text == "text"
    assert parsed_error == (1, "errtext")


@patch("finesse.hardware.opus.em27.logging.warning")
def test_parse_response_bad_id(warning_mock: Mock) -> None:
    """Test that parse_response() can handle <td> tags with unexpected id values."""
    response = _get_opus_html(
        EM27Status.CONNECTING.value,
        "text",
        1,
        "errtext",
        '<td id="MADE_UP">something</td>',
    )
    parsed_status, parsed_text, parsed_error = parse_response(response)
    assert parsed_status == EM27Status.CONNECTING
    assert parsed_text == "text"
    assert parsed_error == (1, "errtext")
    warning_mock.assert_called()


@patch("finesse.hardware.opus.em27.parse_response")
def test_on_reply_received_no_error(
    parse_response_mock: Mock, opus: OPUSInterface, sendmsg_mock: Mock, qtbot
) -> None:
    """Test the _on_reply_received() method works when no error occurs."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # NB: These values are of the wrong type, but it doesn't matter here
    parse_response_mock.return_value = ("status", "text", "error")

    # Check the correct pubsub message is sent
    opus._on_reply_received(reply, "hello")
    sendmsg_mock.assert_called_once_with(
        "opus.response.hello", status="status", text="text", error="error"
    )


@patch("finesse.hardware.opus.em27.parse_response")
def test_on_reply_received_network_error(
    parse_response_mock: Mock, opus: OPUSInterface, qtbot
) -> None:
    """Test the _on_reply_received() method handles network errors."""
    reply = MagicMock()
    reply.error = QNetworkReply.NetworkError.HostNotFoundError
    reply.errorString("Something went wrong")

    with patch.object(opus, "error_occurred") as error_occurred_mock:
        opus._on_reply_received(reply, "hello")
        error_occurred_mock.assert_called_once()


@patch("finesse.hardware.opus.em27.parse_response")
def test_on_reply_received_exception(
    parse_response_mock: Mock, opus: OPUSInterface, qtbot
) -> None:
    """Test that the _on_reply_received() method catches parsing errors."""
    reply = MagicMock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError

    # Make parse_response() raise an exception
    error = Exception()
    parse_response_mock.side_effect = error

    with patch.object(opus, "error_occurred") as error_occurred_mock:
        opus._on_reply_received(reply, "hello")

        # Check the error was caught
        error_occurred_mock.assert_called_once_with(error)
