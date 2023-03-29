"""Provides a base class for interfacing with the OPUS program."""
import logging
import traceback

from pubsub import pub
from PySide6.QtCore import QObject


class OPUSInterfaceBase(QObject):
    """Base class providing an interface to the OPUS program."""

    def __init__(self) -> None:
        """Create a new OPUSInterfaceBase."""
        super().__init__()
        pub.subscribe(self.request_command, "opus.request")

    def error_occurred(self, exception: BaseException) -> None:
        """Signal that an error occurred."""
        traceback_str = "".join(traceback.format_tb(exception.__traceback__))

        # Write details including stack trace to program log
        logging.error(f"Error during OPUS request: {traceback_str}")

        # Notify listeners
        pub.sendMessage("opus.error", message=str(exception))

    def request_command(self, command: str) -> None:
        """Request that OPUS run the specified command.

        Note that we treat "status" as a command, even though it requires a different
        URL to access.

        Args:
            command: Name of command to run
        """
        raise NotImplementedError("request_command() must be overridden by subclass")
