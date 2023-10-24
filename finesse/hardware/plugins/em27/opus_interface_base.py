"""Provides a base class for interfacing with the OPUS program."""
import logging
import traceback
from abc import ABC, abstractmethod

from pubsub import pub


class OPUSInterfaceBase(ABC):
    """Base class providing an interface to the OPUS program."""

    def __init__(self) -> None:
        """Create a new OPUSInterfaceBase."""
        super().__init__()
        pub.subscribe(self.request_command, "opus.request")

    @abstractmethod
    def request_command(self, command: str) -> None:
        """Request that OPUS run the specified command.

        Note that we treat "status" as a command, even though it requires a different
        URL to access.

        Args:
            command: Name of command to run
        """

    @staticmethod
    def error_occurred(error: BaseException) -> None:
        """Signal that an error occurred."""
        traceback_str = "".join(traceback.format_tb(error.__traceback__))

        # Write details including stack trace to program log
        logging.error(f"Error during OPUS request: {traceback_str}")

        # Notify listeners
        pub.sendMessage("opus.error", error=error)
