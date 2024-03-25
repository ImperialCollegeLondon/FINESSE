"""Provides a base class for interfacing with the FTSW500 program."""

from __future__ import annotations

from abc import abstractmethod

from finesse.hardware.plugins.spectrometer.spectrometer_base import SpectrometerBase


class FTSW500Error(Exception):
    """Indicates that an error occurred with an FTSW500 device."""

    @classmethod
    def from_response(cls, errcode: int, errtext: str) -> FTSW500Error:
        """Create an FTSW500Error from the information given in the device response."""
        return cls(f"Error {errcode}: {errtext}")


class FTSW500InterfaceBase(SpectrometerBase):
    """Base class providing an interface to the FTSW500 program."""

    def connect(self) -> None:
        """Connect to the spectrometer."""
        self.request_command(b"clickConnectButton\n")

    def start_measuring(self) -> None:
        """Start a new measurement."""
        self.request_command(b"clickStartAcquisitionButton\n")

    def stop_measuring(self) -> None:
        """Stop the current measurement."""
        self.request_command(b"clickStopAcquisitionButton\n")

    @abstractmethod
    def request_command(self, command: bytes) -> None:
        """Request that FTSW500 run the specified command.

        Args:
            command: Name of command to run
        """
