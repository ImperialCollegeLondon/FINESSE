"""Provides a base class for interfacing with the OPUS program."""
from __future__ import annotations

import logging
import traceback
from abc import ABC, abstractmethod

from pubsub import pub

from finesse.em27_info import EM27Status


class OPUSError(Exception):
    """Indicates that an error occurred with an OPUS device."""

    @classmethod
    def from_response(cls, errcode: int, errtext: str) -> OPUSError:
        """Create an OPUSError from the information given in the device response."""
        return cls(f"Error {errcode}: {errtext}")


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
    def send_response(command: str, status: EM27Status, text: str) -> None:
        """Broadcast the device's response via pubsub."""
        pub.sendMessage(f"opus.response.{command}", status=status, text=text)

    @staticmethod
    def error_occurred(error: BaseException) -> None:
        """Signal that an error occurred."""
        traceback_str = "".join(traceback.format_tb(error.__traceback__))

        # Write details including stack trace to program log
        logging.error(f"Error during OPUS request: {traceback_str}")

        # Notify listeners
        pub.sendMessage("opus.error", error=error)
