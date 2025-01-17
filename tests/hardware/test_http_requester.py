"""Tests for the HTTPRequester class."""

from unittest.mock import MagicMock, Mock, patch

from frog.hardware.http_requester import HTTPRequester


@patch("frog.hardware.http_requester.QNetworkRequest")
def test_make_request(request_mock: Mock, qtbot) -> None:
    """Test the make_request() method."""
    URL = "https://example.com"
    requester = HTTPRequester(2.0)
    request = MagicMock()
    request_mock.return_value = request

    with patch.object(requester, "_manager") as manager_mock:
        callback = MagicMock()
        reply = MagicMock()
        manager_mock.get.return_value = reply
        requester.make_request(URL, callback)
        request_mock.assert_called_once_with(URL)
        request.setTransferTimeout.assert_called_once_with(2000)
        manager_mock.get.assert_called_once_with(request)
        assert reply.finished.connect.call_count == 1
        reply.finished.connect.call_args.args[0]()
        callback.assert_called_once_with(reply)
