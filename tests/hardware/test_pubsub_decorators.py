"""Tests for the pubsub_errors decorator."""

from collections.abc import Callable
from unittest.mock import MagicMock

from finesse.hardware.pubsub_decorators import pubsub_errors

ERROR_TOPIC = "my_topic.error"


class Dummy:
    """A class for testing decorators on class methods."""

    error_topic = ERROR_TOPIC

    def __init__(self, func_mock: MagicMock) -> None:
        """Create a new Dummy object.

        Args:
            func_mock: Function to call in member functions
        """
        self.func_mock = func_mock

    def func(self, *args, **kwargs):
        """Invokes func_mock with the specified arguments."""
        return self.func_mock(*args, **kwargs)


def _test_decorator_error(decorator: Callable, sendmsg_mock: MagicMock) -> None:
    error = Exception()
    func_mock = MagicMock(side_effect=error)
    dummy = Dummy(func_mock)
    decorated_func = decorator(dummy.func)

    assert decorated_func(dummy, 1, 2, 3) is None
    func_mock.assert_called_once_with(dummy, 1, 2, 3)
    sendmsg_mock.assert_called_once_with(ERROR_TOPIC, error=error)


def test_pubsub_errors_error(sendmsg_mock: MagicMock) -> None:
    """Test pubsub_errors for when an error occurs."""
    _test_decorator_error(pubsub_errors, sendmsg_mock)


def test_pubsub_errors_no_error(sendmsg_mock: MagicMock) -> None:
    """Test pubsub_errors for when no errors occur."""
    func_mock = MagicMock(return_value="MAGIC")
    dummy = Dummy(func_mock)
    decorated_func = pubsub_errors(dummy.func)

    assert decorated_func(dummy, 1, 2, 3) == "MAGIC"
    func_mock.assert_called_once_with(dummy, 1, 2, 3)
    sendmsg_mock.assert_not_called()
