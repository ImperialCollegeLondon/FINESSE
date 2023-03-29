"""An interface for using the YAML-formatted measure scripts.

This includes code for parsing and running the scripts.
"""
from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass
from io import TextIOBase
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Sequence, Union

import yaml
from pubsub import pub
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget
from schema import And, Or, Schema, SchemaError
from statemachine import State, StateMachine

from ...config import ANGLE_PRESETS
from ..error_message import show_error_message


@dataclass
class Measurement:
    """Represents a single step (i.e. angle + number of measurements)."""

    angle: Union[str, float]
    """Either an angle in degrees or the name of a preset angle."""

    measurements: int
    """The number of times to record a measurement at this position."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert this object to a dict."""
        return {"angle": self.angle, "measurements": self.measurements}


class Script:
    """Represents a measure script, including its file path and data."""

    def __init__(
        self, path: Path, repeats: int, sequence: Sequence[Dict[str, Any]]
    ) -> None:
        """Create a new Script.

        Args:
            path: The file path to this measure script
            repeats: The number of times to repeat the sequence of measurements
            sequence: Different measurements (i.e. angle + num measurements) to record
        """
        self.path = path
        self.repeats = repeats
        self.sequence = [Measurement(**val) for val in sequence]
        self.runner: Optional[ScriptRunner] = None

    def __iter__(self) -> Iterator[Measurement]:
        """Get an iterator for the measurements."""
        return itertools.chain.from_iterable(
            itertools.repeat(self.sequence, self.repeats)
        )

    def run(self, parent: Optional[QWidget] = None) -> None:
        """Run this measure script."""
        logging.info(f"Running {self.path}")
        self.runner = ScriptRunner(self, parent=parent)
        self.runner.start_moving()

    @classmethod
    def try_load(cls, parent: QWidget, file_path: Path) -> Optional[Script]:
        """Try to load a measure script at the specified path.

        Args:
            parent: The parent widget (for error messages shown)
            file_path: The path to the script to be loaded
        Returns:
            A Script if successful, else None
        """
        try:
            with open(file_path, "r") as f:
                return cls(file_path, **parse_script(f))
        except OSError as e:
            show_error_message(parent, f"Error: Could not read {file_path}: {str(e)}")
        except ParseError:
            show_error_message(parent, f"Error: {file_path} is in an invalid format")
        return None


class ParseError(Exception):
    """An error occurred while parsing a measure script."""

    def __init__(_) -> None:
        """Create a new ParseError."""
        super().__init__("Error parsing measure script")


def parse_script(script: Union[str, TextIOBase]) -> Dict[str, Any]:
    """Parse a measure script.

    Args:
        script: The contents of the script as YAML or a stream containing YAML
    Raises:
        ParseError: The script's contents were invalid
    """
    valid_float = And(float, lambda f: 0.0 <= f < 360.0)
    valid_preset = And(str, lambda s: s in ANGLE_PRESETS)
    measurements_type = And(int, lambda x: x > 0)
    nonempty_list = And(list, lambda x: x)

    schema = Schema(
        {
            "repeats": measurements_type,
            "sequence": And(
                nonempty_list,
                [
                    {
                        "angle": Or(valid_float, valid_preset),
                        "measurements": measurements_type,
                    }
                ],
            ),
        }
    )

    try:
        return schema.validate(yaml.safe_load(script))
    except (yaml.YAMLError, SchemaError) as e:
        raise ParseError() from e


def _poll_em27_status() -> None:
    """Request the EM27's status from OPUS."""
    pub.sendMessage("opus.request", command="status")


class ScriptRunner(StateMachine):
    """A class for running measure scripts.

    The ScriptRunner is a finite state machine. Besides the one initial state, the
    runner can either be in a "moving" state (i.e. the motor is moving) or a "measuring"
    state (i.e. the motor is stationary and the EM27 is recording a measurement).
    """

    not_running = State("Not running", initial=True)
    """State indicating that the script is not yet running or has finished."""
    moving = State("Moving")
    """State indicating that the motor is moving."""
    measuring = State("Measuring")
    """State indicating that a measurement is taking place."""

    start_moving = not_running.to(
        moving, before=lambda: pub.sendMessage("measure_script.begin")
    )
    """Start moving the motor to the required angle for the current measurement."""
    start_measuring = moving.to(measuring)
    """Start recording the current measurement."""
    repeat_measuring = measuring.to(measuring)
    """Record another measurement at the same angle."""
    cancel_measuring = measuring.to(
        not_running, after=lambda: pub.sendMessage("opus.request", command="cancel")
    )
    """Cancel the current measurement."""
    start_next_move = measuring.to(moving)
    """Trigger a move to the angle for the next measurement."""
    finish = moving.to(not_running)
    """To be called when all measurements are complete."""

    def __init__(
        self,
        script: Script,
        min_poll_interval: float = 1.0,
        parent: Optional[QWidget] = None,
    ) -> None:
        """Create a new ScriptRunner.

        Note that the EM27 often takes more than one second to respond to requests,
        hence why we set a minimum polling interval rather than an absolute one.

        Args:
            script: The script to run
            min_poll_interval: Minimum rate at which to poll EM27 (seconds)
            parent: The parent widget

        Todo:
            Error handling for the stepper motor
        """
        self.script = script
        """The running script."""
        self.measurement_iter = iter(self.script)
        """An iterator yielding the required sequence of measurements."""
        self.parent = parent
        """The parent widget."""

        self.current_measurement: Measurement
        """The current measurement to acquire."""
        self.current_measurement_count: int
        """How many times a measurement has been recorded at the current angle."""

        self._measure_poll_timer = QTimer()
        """A timer which repeatedly polls the EM27."""
        self._measure_poll_timer.setSingleShot(True)
        self._measure_poll_timer.setInterval(round(1000 * min_poll_interval))
        self._measure_poll_timer.timeout.connect(_poll_em27_status)  # type: ignore

        # Send stop command in case motor is moving
        pub.sendMessage("serial.stepper_motor.stop")

        super().__init__()

    def on_enter_state(self, target: State) -> None:
        """Log the state every time it changes.

        This is just a placeholder so we can see the measure scripts running.
        """
        logging.info(f"Measure script: Entering state {target.name}")

    def on_enter_not_running(self, event: str) -> None:
        """If finished, unsubscribe from pubsub messages and send message."""
        if event == "__initial__":
            # If this is the first state, do nothing
            return

        # Stepper motor messages
        pub.unsubscribe(self.start_measuring, "serial.stepper_motor.move.end")

        # EM27 messages
        pub.unsubscribe(self._measuring_error, "opus.error")
        pub.unsubscribe(self._measuring_started, "opus.response.start")
        pub.unsubscribe(self._status_received, "opus.response.status")

        # Send message signalling that the measure script is no longer running
        pub.sendMessage("measure_script.end")

    def on_exit_not_running(self) -> None:
        """Subscribe to pubsub messages for the stepper motor and OPUS."""
        # Listen for stepper motor messages (TODO: add error handling)
        pub.subscribe(self.start_measuring, "serial.stepper_motor.move.end")

        # Listen for EM27 messages
        pub.subscribe(self._measuring_error, "opus.error")
        pub.subscribe(self._measuring_started, "opus.response.start")
        pub.subscribe(self._status_received, "opus.response.status")

    def _load_next_measurement(self) -> bool:
        """Load the next measurement in the sequence.

        Returns:
            False if there are no more measurements
        """
        try:
            self.current_measurement = next(self.measurement_iter)
            self.current_measurement_count = 0
            return True
        except StopIteration:
            return False

    def on_enter_moving(self) -> None:
        """Try to load the next measurement and start the next movement.

        If there are no more measurements, the ScriptRunner will return to a not_running
        state.
        """
        if not self._load_next_measurement():
            self.finish()
            return

        # Start moving the stepper motor
        pub.sendMessage(
            "serial.stepper_motor.move.begin", target=self.current_measurement.angle
        )

        # Flag that we want a message when the movement has stopped
        pub.sendMessage("serial.stepper_motor.notify_on_stopped")

    def on_enter_measuring(self) -> None:
        """Tell the EM27 to start a new measurement.

        NB: This is also invoked on repeat measurements
        """
        pub.sendMessage("opus.request", command="start")

    def on_exit_measuring(self) -> None:
        """Ensure that the polling timer is stopped."""
        self._measure_poll_timer.stop()

    def _measuring_started(
        self,
        status: int,
        text: str,
        error: Optional[tuple[int, str]],
        url: str,
    ):
        """Start polling the EM27 so we know when the measurement is finished."""
        if error:
            self._on_em27_error_message(*error)
        else:
            _poll_em27_status()

    def _status_received(
        self,
        status: int,
        text: str,
        error: Optional[tuple[int, str]],
        url: str,
    ):
        """Move on to the next measurement if the measurement has finished."""
        if error:
            self._on_em27_error_message(*error)
            return

        if status == 2:  # "connected" state, indicating measurement is finished
            self._measuring_end()
        else:
            # Poll again later
            self._measure_poll_timer.start()

    def _on_em27_error(self, message: str) -> None:
        """Cancel current measurement and show an error message to the user."""
        self.cancel_measuring()

        show_error_message(
            self.parent,
            f"EM27 error occurred. Measure script will stop running.\n\n{message}",
        )

    def _on_em27_error_message(self, errcode: int, errmsg: str) -> None:
        """Error reported by EM27 system."""
        self._on_em27_error(f"Error {errcode}: {errmsg}")

    def _measuring_error(self, error: BaseException) -> None:
        """Log errors from OPUS."""
        self._on_em27_error(str(error))

    def _measuring_end(self) -> None:
        """Move onto the next measurement or perform another measurement here."""
        self.current_measurement_count += 1
        if self.current_measurement_count == self.current_measurement.measurements:
            self.start_next_move()
        else:
            self.repeat_measuring()
