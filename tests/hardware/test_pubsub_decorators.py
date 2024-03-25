"""Tests for the pubsub_errors decorator."""

from collections.abc import Callable
from unittest.mock import MagicMock

from finesse.hardware.pubsub_decorators import pubsub_errors

ERROR_TOPIC = "my_topic.error"
SUCCESS_TOPIC = "my_topic.success"


def _test_decorator_error(decorator: Callable, sendmsg_mock: MagicMock) -> None:
    error = Exception()
    func_mock = MagicMock()

    def func(*args, **kwargs):
        func_mock(*args, **kwargs)
        raise error

    decorated_func = decorator(func)
    assert decorated_func(1, 2, 3) is None
    func_mock.assert_called_once_with(1, 2, 3)
    sendmsg_mock.assert_called_once_with(ERROR_TOPIC, error=error)


def test_pubsub_errors_error(sendmsg_mock: MagicMock) -> None:
    """Test pubsub_errors for when an error occurs."""
    _test_decorator_error(pubsub_errors(ERROR_TOPIC), sendmsg_mock)


def test_pubsub_errors_no_error(sendmsg_mock: MagicMock) -> None:
    """Test pubsub_errors for when no errors occur."""
    func_mock = MagicMock()

    def func(*args, **kwargs):
        func_mock(*args, **kwargs)
        return "MAGIC"

    decorated_func = pubsub_errors(ERROR_TOPIC)(func)
    assert decorated_func(1, 2, 3) == "MAGIC"
    func_mock.assert_called_once_with(1, 2, 3)
    sendmsg_mock.assert_not_called()
