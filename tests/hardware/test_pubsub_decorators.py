"""Tests for the pubsub_errors decorator."""

from collections.abc import Callable
from unittest.mock import MagicMock, Mock, patch

from finesse.hardware.pubsub_decorators import PubSubErrorWrapper, pubsub_errors

ERROR_TOPIC = "my_topic.error"


class Dummy(PubSubErrorWrapper):
    """A class for testing decorators on class methods."""

    def __init__(self, func_mock: MagicMock, **extra_error_kwargs) -> None:
        """Create a new Dummy object.

        Args:
            func_mock: Function to call in member functions
            extra_error_kwargs: Extra arguments for pub.sendMessage
        """
        super().__init__(error_topic=ERROR_TOPIC, **extra_error_kwargs)
        self.func_mock = func_mock

    def func(self, *args, **kwargs):
        """Invokes func_mock with the specified arguments."""
        return self.func_mock(*args, **kwargs)


def _test_decorator_error(decorator: Callable) -> None:
    error = Exception()
    func_mock = MagicMock(side_effect=error)
    dummy = Dummy(func_mock)
    with patch.object(dummy, "report_error") as report_mock:
        decorated_func = decorator(dummy.func)

        assert decorated_func(dummy, 1, 2, 3) is None
        func_mock.assert_called_once_with(dummy, 1, 2, 3)
        report_mock.assert_called_once_with(error)


def test_pubsub_errors_error() -> None:
    """Test pubsub_errors for when an error occurs."""
    _test_decorator_error(pubsub_errors)


def test_pubsub_errors_no_error() -> None:
    """Test pubsub_errors for when no errors occur."""
    func_mock = MagicMock(return_value="MAGIC")
    dummy = Dummy(func_mock)
    with patch.object(dummy, "report_error") as report_mock:
        decorated_func = pubsub_errors(dummy.func)

        assert decorated_func(dummy, 1, 2, 3) == "MAGIC"
        func_mock.assert_called_once_with(dummy, 1, 2, 3)
        report_mock.assert_not_called()


@patch("finesse.hardware.pubsub_decorators.logging")
def test_report_error(logging_mock: Mock, sendmsg_mock: MagicMock) -> None:
    """Test PubSubErrorWrapper's report_error() method."""
    wrapper = PubSubErrorWrapper("error_topic", extra_arg="value")
    error = Exception()
    wrapper.report_error(error)
    sendmsg_mock.assert_called_once_with("error_topic", error=error, extra_arg="value")
    logging_mock.error.assert_called()
