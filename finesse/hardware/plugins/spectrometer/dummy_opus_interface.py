"""Provides a dummy EM27 device for interfacing with."""

import logging
from collections.abc import Callable
from enum import Enum

from PySide6.QtCore import QTimer
from statemachine import State, StateMachine
from statemachine.exceptions import TransitionNotAllowed

from finesse.hardware.plugins.spectrometer.opus_interface_base import (
    OPUSError,
    OPUSInterfaceBase,
)
from finesse.spectrometer_status import SpectrometerStatus


class OPUSErrorInfo(Enum):
    """Represents an error code and description for OPUS errors.

    The codes and descriptions are taken from the manual.
    """

    NO_ERROR = (0, "No error")
    NOT_IDLE = (1, "Status is not 'Idle' although required for current command")
    NOT_RUNNING = (2, "Status is not 'Running' although required for current command")
    NOT_RUNNING_OR_FINISHING = (
        3,
        "Status is not 'Running' or 'Finishing' although required for current command",
    )
    UNKNOWN_COMMAND = (4, "Unknown command")
    WEBSITE_NOT_FOUND = (5, "Website not found")
    NO_RESULT = (6, "No result available")
    NOT_CONNECTED = (7, "System not connected")

    def to_tuple(self) -> tuple[int, str] | None:
        """Convert to a (code, message) tuple or None if no error."""
        if self == OPUSErrorInfo.NO_ERROR:
            return None
        return self.value


class OPUSStateMachine(StateMachine):
    """An FSM for keeping track of the internal state of the mock device."""

    idle = State("Idle", SpectrometerStatus.IDLE, initial=True)
    connecting = State("Connecting", SpectrometerStatus.CONNECTING)
    connected = State("Connected", SpectrometerStatus.CONNECTED)
    measuring = State("Measuring", SpectrometerStatus.MEASURING)
    finishing = State("Finishing current measurement", SpectrometerStatus.FINISHING)
    cancelling = State("Cancelling", SpectrometerStatus.CANCELLING)
    # The manual also describes an "Undefined" state, which we aren't using

    _start_connecting = idle.to(connecting)
    _finish_connecting = connecting.to(connected)

    start = connected.to(measuring)
    _start_finishing_measuring = measuring.to(finishing)
    _finish_measuring = finishing.to(connected)
    _cancel_measuring = measuring.to(cancelling)
    _reset_after_cancelling = cancelling.to(connected)

    def __init__(
        self, measure_duration: float, measure_finish_callback: Callable
    ) -> None:
        """Create a new OPUSStateMachine.

        The state diagram looks like this:

        ![](../../../../../OPUSStateMachine.png)

        Args:
            measure_duration: How long a single measurement takes (seconds)
            measure_finish_callback: Called when measurement completes successfully
        """
        self.measure_finish_callback = measure_finish_callback

        self.measure_timer = QTimer()
        """Timer signalling the end of a measurement."""
        self.measure_timer.setInterval(round(measure_duration * 1000))
        self.measure_timer.setSingleShot(True)
        self.measure_timer.timeout.connect(self.stop)

        super().__init__()

    def connect(self) -> None:
        """Connect to the device."""
        self._start_connecting()
        self._finish_connecting()

    def cancel(self) -> None:
        """Cancel the current measurement."""
        self._cancel_measuring()
        self._reset_after_cancelling()
        logging.info("Cancelling current measurement")

    def stop(self) -> None:
        """Finish measurement successfully."""
        self._start_finishing_measuring()
        self._finish_measuring()

    def on_enter_measuring(self) -> None:
        """Start the measurement timer."""
        self.measure_timer.start()

    def on_exit_measuring(self) -> None:
        """Stop the measurement timer."""
        self.measure_timer.stop()
        self.measure_finish_callback()

    def on_enter_state(self, target: State) -> None:
        """Log all state transitions."""
        logging.info(f"Current state: {target.name}")


class DummyOPUSInterface(
    OPUSInterfaceBase,
    description="Dummy OPUS device",
    parameters={"measure_duration": "Measurement duration in seconds"},
):
    """A mock version of the OPUS API for testing purposes."""

    _COMMAND_ERRORS = {
        "cancel": OPUSErrorInfo.NOT_RUNNING,
        "stop": OPUSErrorInfo.NOT_RUNNING_OR_FINISHING,
        "start": OPUSErrorInfo.NOT_CONNECTED,
        "connect": OPUSErrorInfo.NOT_IDLE,
    }
    """The error thrown by each command when in an invalid state."""

    def __init__(self, measure_duration: float = 1.0) -> None:
        """Create a new DummyOPUSInterface.

        Args:
            measure_duration: How long a single measurement takes (seconds)
        """
        super().__init__()

        self.last_error = OPUSErrorInfo.NO_ERROR
        """The last error which occurred."""
        self.state_machine = OPUSStateMachine(
            measure_duration, self._measuring_finished
        )
        """An object representing the internal state of the device."""

    def _run_command(self, command: str) -> None:
        """Try to run the specified command.

        If the device is not in the correct state, self.last_error will be changed.

        Args:
            command: The command to run
        """
        fun = getattr(self.state_machine, command)

        self.last_error = OPUSErrorInfo.NO_ERROR
        try:
            fun()
        except TransitionNotAllowed:
            self.last_error = self._COMMAND_ERRORS[command]

    def request_command(self, command: str) -> None:
        """Execute the specified command on the device.

        Note that we treat "status" as a command, even though it requires a different
        URL to access.

        Args:
            command: The command to run
        Raises:
            OPUSError: If the device is in the wrong state for this command
        """
        if command == "status":
            if self.state_machine.current_state == OPUSStateMachine.idle:
                self.last_error = OPUSErrorInfo.NOT_CONNECTED
        elif command in self._COMMAND_ERRORS:
            self._run_command(command)
        else:
            self.last_error = OPUSErrorInfo.UNKNOWN_COMMAND

        if errinfo := self.last_error.to_tuple():
            raise OPUSError.from_response(*errinfo)

        # Broadcast the response for the command
        self.send_response(command, self.state_machine.current_state.value)

    def _measuring_finished(self) -> None:
        """Finish measurement successfully."""
        self.last_error = OPUSErrorInfo.NO_ERROR
        logging.info("Measurement complete")
