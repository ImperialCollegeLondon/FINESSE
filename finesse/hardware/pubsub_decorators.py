"""Provides a decorator for catching and forwarding errors via pubsub."""
from collections.abc import Callable

from decorator import decorator
from pubsub import pub


def pubsub_errors(error_topic: str) -> Callable:
    """Catch exceptions and broadcast via pubsub.

    Args:
        error_topic: The topic name on which to broadcast errors
    """

    def wrapped(func: Callable, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            pub.sendMessage(error_topic, error=error)

    return decorator(wrapped)
