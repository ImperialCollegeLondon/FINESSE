"""Tests for the pubsub_errors decorator."""
from unittest.mock import MagicMock, Mock

from finesse.hardware.pubsub_decorators import pubsub_errors


def test_pubsub_errors_no_error(sendmsg_mock: Mock) -> None:
    """Test for when no errors occur."""
    func_mock = MagicMock()

    def func(*args, **kwargs):
        func_mock(*args, **kwargs)
        return "MAGIC"

    decorated_func = pubsub_errors("my_topic.error")(func)
    assert decorated_func(1, 2, 3) == "MAGIC"
    func_mock.assert_called_once_with(1, 2, 3)
    sendmsg_mock.assert_not_called()


def test_pubsub_errors_error(sendmsg_mock: Mock) -> None:
    """Test for when an error occurs."""
    error = Exception()
    func_mock = MagicMock()

    def func(*args, **kwargs):
        func_mock(*args, **kwargs)
        raise error

    decorated_func = pubsub_errors("my_topic.error")(func)
    assert decorated_func(1, 2, 3) is None
    func_mock.assert_called_once_with(1, 2, 3)
    sendmsg_mock.assert_called_once_with("my_topic.error", error=error)
