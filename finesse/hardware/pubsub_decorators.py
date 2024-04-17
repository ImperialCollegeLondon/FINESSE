"""Provides a decorator for catching and forwarding errors via pubsub."""

import logging
import traceback
from collections.abc import Callable

from decorator import decorator
from frozendict import frozendict
from pubsub import pub


class PubSubErrorWrapper:
    """A class to help with catching errors and broadcasting them via pubsub.

    Classes needing the pubsub_errors() decorator should inherit from this class.
    """

    def __init__(self, error_topic: str, **extra_error_kwargs) -> None:
        """Create a new ErrorWrapper.

        Args:
            error_topic: The topic on which to broadcast error messages
            extra_error_kwargs: Extra arguments to pass via pub.sendMessage
        """
        self._error_topic = error_topic
        self._extra_error_kwargs = frozendict(extra_error_kwargs)

    def report_error(self, error: Exception) -> None:
        """Signal that an error occurred."""
        traceback_str = "".join(traceback.format_tb(error.__traceback__))

        # Write details including stack trace to program log
        logging.error(
            f"Caught error ({self._error_topic}): {error!s}\n\n{traceback_str}"
        )

        # Notify listeners
        pub.sendMessage(self._error_topic, error=error, **self._extra_error_kwargs)


@decorator
def pubsub_errors(func: Callable, *args, **kwargs):
    """Catch exceptions and broadcast via pubsub.

    Args:
        func: The function to decorate
        args: Arguments for func
        kwargs: Keyword arguments for func
    """
    try:
        return func(*args, **kwargs)
    except Exception as error:
        # **HACK**: Depending on how the decorator is used, func will either be a member
        # function or a regular function whose first argument is self. Unfortunately it
        # means that there doesn't seem to be a clean way to access the parent object,
        # so we have to resort to this smelly hack to access the report_error() member
        # function.
        obj = getattr(func, "__self__", None) or args[0]
        obj.report_error(error)
