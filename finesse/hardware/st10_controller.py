"""Code for interfacing with the ST10-Q-NN stepper motor controller.

Applied Motions have their own bespoke programming language ("Q") for interfacing with
their devices, of which we're only using a small portion here.

The specification is available online:
    https://appliedmotion.s3.amazonaws.com/Host-Command-Reference_920-0002W_0.pdf
"""

import logging
from queue import Queue
from typing import Any, Optional, Union

from pubsub import pub
from PySide6.QtCore import QThread, Signal, Slot
from serial import Serial, SerialException, SerialTimeoutException

from .stepper_motor_base import StepperMotorBase


class ST10ControllerError(SerialException):
    """Indicates that an error has occurred with the ST10 controller."""


_ASYNC_MAGIC = "Z"


class _SerialReader(QThread):
    """For background reading of serial device."""

    async_read_completed = Signal()
    """Indicates that an asynchronous read has finished."""

    def __init__(self, serial: Serial, sync_timeout: float) -> None:
        """Create a new _SerialReader.

        Args:
            serial: Serial device
            sync_timeout: Read timeout for synchronous requests
        """
        super().__init__()

        self.serial = serial
        self.sync_timeout = sync_timeout
        self.out_queue: Queue = Queue()
        self.stopping = False
        self.async_waiters = 0

    def __del__(self) -> None:
        """Wait for the thread to stop on exit."""
        self.quit()
        self.wait()

    def quit(self) -> None:
        """Flag that the thread is stopping so we can ignore exceptions."""
        self.stopping = True
        super().quit()

    def _read(self) -> str:
        """Read the next message from the device.

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
        """
        raw = self.serial.read_until(b"\r")

        # Check that it hasn't timed out
        if not raw:
            raise SerialTimeoutException()

        logging.debug(f"(ST10) <<< {repr(raw)}")

        try:
            return raw[:-1].decode("ascii")
        except UnicodeDecodeError:
            raise ST10ControllerError(f"Invalid message received: {repr(raw)}")

    def _process_read(self) -> bool:
        """Process a single read, either synchronous or asynchronous."""
        try:
            message = self._read()
        except Exception as ex:
            if not self.stopping:
                self.out_queue.put(ex)
            return False

        # TODO: error handling for async?
        if message == _ASYNC_MAGIC and self.async_waiters > 0:
            self.async_waiters -= 1
            self.async_read_completed.emit()
            return True

        # Put the message (or error) into a queue to be returned by read_sync()
        self.out_queue.put(message)
        return True

    def run(self) -> None:
        """Process reads in the background."""
        while self._process_read():
            pass

    def read_sync(self) -> str:
        """Read synchronously from the serial device."""
        try:
            response: Union[str, BaseException] = self.out_queue.get(
                timeout=self.sync_timeout
            )
        except Exception:
            raise SerialTimeoutException()

        if isinstance(response, BaseException):
            raise response

        return response

    def read_async(self) -> None:
        """Read asynchronously from the serial device."""
        self.async_waiters += 1


class ST10Controller(StepperMotorBase):
    """An interface for the ST10-Q-NN stepper motor controller.

    This class allows for moving the mirror to arbitrary positions and retrieving its
    current position.
    """

    STEPS_PER_ROTATION = 50800
    """The total number of steps in one full rotation of the mirror."""

    ST10_MODEL_ID = "107F024"
    """The model and revision number for the ST10 controller we are using."""

    def __init__(self, serial: Serial) -> None:
        """Create a new ST10Controller.

        Args:
            serial: The serial device to communicate with the ST10 controller

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
        """
        self.serial = serial
        timeout = self.serial.timeout
        self.serial.timeout = None

        self._reader = _SerialReader(serial, timeout)
        self._reader.async_read_completed.connect(
            self._async_read_completed
        )  # type: ignore
        self._reader.start()

        # Check that we are connecting to an ST10
        self._check_device_id()

        # In case the motor is still moving, stop it now
        self.stop_moving()

        # Move mirror to home position
        self._home_and_reset()

        super().__init__()

    @staticmethod
    def create(
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        *serial_args: Any,
        **serial_kwargs: Any,
    ):
        """Create a new ST10Controller with the specified serial device properties.

        Args:
            port: Serial port name
            baudrate: Serial port baudrate
            timeout: How long to wait for read operations (seconds)
            serial_args: Extra arguments to Serial constructor
            serial_kwargs: Extra keyword arguments to Serial constructor
        """
        if "write_timeout" not in serial_kwargs:
            serial_kwargs["write_timeout"] = timeout

        serial = Serial(port, baudrate, *serial_args, timeout=timeout, **serial_kwargs)
        return ST10Controller(serial)

    def __del__(self) -> None:
        """Leave mirror facing downwards when finished.

        This prevents dust accumulating.
        """
        try:
            self.stop_moving()
            self.move_to("nadir")
        except Exception as e:
            logging.error(f"Failed to reset mirror to downward position: {e}")

        self.serial.close()

    @Slot()
    def _async_read_completed(self, topic: str) -> None:
        pub.sendMessage(topic)

    def _check_device_id(self) -> None:
        """Check that the ID is the correct one for an ST10.

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: The device ID is not for an ST10
        """
        # Request model and revision
        self._write("MV")
        if self._read_sync() != self.ST10_MODEL_ID:
            raise ST10ControllerError("Device ID indicates this is not an ST10")

    def _get_input_status(self, index: int) -> bool:
        """Read the status of the device's inputs.

        The inputs to the controller are boolean values represented as a series of zeros
        (==closed) and ones (==open). They include digital inputs, as well as other
        properties like alarm status. The exact meaning seems to vary between boards.

        Args:
            index: Which boolean value in the input status array to check
        """
        input_status = self._request_value("IS")
        return input_status[index] == "1"

    @property
    def steps_per_rotation(self) -> int:
        """Get the number of steps that correspond to a full rotation."""
        return self.STEPS_PER_ROTATION

    def _home_and_reset(self) -> None:
        """Return the stepper motor to its home position and reset the counter.

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
        """
        # If the third (boolean) value of the input status array is set, then move the
        # motor first. I don't know what the input status actually means, but this is
        # how it was done in the old program, so I'm copying it here.
        if self._get_input_status(3):
            self._relative_move(-5000)

        # Home the motor, leaving mirror facing upwards. The command means "seek home
        # until input 6 is high" (the input is an optoswitch).
        self._write_check("SH6H")

        # Turn mirror so it's facing down
        self._relative_move(-30130)

        # Tell the controller that this is step 0 ("set variable SP to 0")
        self._write_check("SP0")

    def _relative_move(self, steps: int) -> None:
        """Move the stepper motor to the specified relative position.

        Args:
            steps: Number of steps to move by

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
        """
        # "Feed to length"
        self._write_check(f"FL{steps}")

    @property
    def step(self) -> int:
        """The current state of the device's step counter.

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
        """
        step = self._request_value("SP")
        try:
            return int(step)
        except ValueError:
            raise ST10ControllerError(f"Invalid value for step received: {step}")

    @step.setter
    def step(self, step: int) -> None:
        """Move the stepper motor to the specified absolute position.

        Args:
            step: Which step position to move to

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
        """
        # "Feed to position"
        self._write_check(f"FP{step}")

    def _send_string(self, string: str) -> None:
        """Request that the device sends string when operations have completed.

        Args:
            string: String to be returned by the device
        """
        # "Send string"
        self._write_check(f"SS{string}")

    def _read_sync(self) -> str:
        """Read the next message from the device synchronously.

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
        """
        return self._reader.read_sync()

    def _read_async(self) -> None:
        """Read from the device asynchronously."""
        self._send_string(_ASYNC_MAGIC)
        return self._reader.read_async()

    def _write(self, message: str) -> None:
        """Send the specified message to the device.

        Raises:
            SerialException: Error communicating with device
            UnicodeEncodeError: Malformed message
        """
        data = f"{message}\r".encode("ascii")
        logging.debug(f"(ST10) >>> {repr(data)}")
        self.serial.write(data)

    def _write_check(self, message: str) -> None:
        """Send the specified message and check whether the device returns an error.

        See _check_response().

        Args:
            message: ASCII-formatted message

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
            UnicodeEncodeError: Message to be sent is malformed
        """
        self._write(message)
        self._check_response()

    def _check_response(self) -> None:
        """Check whether the device has returned an error.

        There are two types of "success" response (ACK):
            - Normal acknowledge ("%"), indicating that the command was received and
              successfully executed
            - Exception acknowledge ("*"), indicating that the command was received and
              added to the execution buffer, i.e. it will be executed after other
              commands. (Why the manual uses the term "exception", who knows, but it
              also indicates success!)

        If an error occurs, the device returns a negative acknowledge (NACK) response,
        which is a "?", followed by an error code, e.g. "?4". The meanings of the error
        codes are listed in the manual linked in the module description.

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Error or malformed message
        """
        response = self._read_sync()

        # Either type of ACK response is acceptable
        if response in ("%", "*"):
            return

        # An error occurred (NACK)
        if response[0] == "?":
            raise ST10ControllerError(
                f"Device returned an error (code: {response[1:]})"
            )

        raise ST10ControllerError(f"Unexpected response from device: {response}")

    def _request_value(self, name: str) -> str:
        """Request a named value from the device.

        You can request the values of various variables, which all seem to have
        two-letter names.

        Args:
            name: Variable name

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for response from device
            ST10ControllerError: Malformed message received from device
            UnicodeEncodeError: Message to be sent is malformed
        """
        self._write(name)
        response = self._read_sync()
        if not response.startswith(f"{name}="):
            raise ST10ControllerError(f"Unexpected response when querying value {name}")

        return response[len(name) + 1 :]

    def stop_moving(self) -> None:
        """Immediately stop moving the motor."""
        self._write_check("ST")

    def wait_until_stopped(self, timeout: Optional[float] = None) -> None:
        """Wait until the motor has stopped moving.

        Args:
            timeout: Time to wait for motor to finish moving (None == forever)

        Raises:
            SerialException: Error communicating with device
            SerialTimeoutException: Timed out waiting for motor to finish moving
            ST10ControllerError: Malformed message received from device
        """
        # Tell device to send "X" when current operations are complete
        self._send_string("X")

        # Set temporary timeout
        old_timeout, self.serial.timeout = self.serial.timeout, timeout
        try:
            if self._read_sync() != "X":
                raise ST10ControllerError(
                    "Invalid response received when waiting for X"
                )
        finally:
            # Restore previous timeout setting
            self.serial.timeout = old_timeout


if __name__ == "__main__":
    import sys

    print(f"Connecting to device {sys.argv[1]}...")
    dev = ST10Controller.create(sys.argv[1])
    print("Done. Homing...")

    dev.wait_until_stopped()
    print("Homing complete")
    print(f"Current angle: {dev.angle}°")

    angles = (0.0, 90.0, 180.0, "hot_bb")
    for ang in angles:
        print(f"Moving to {ang}")
        dev.move_to(ang)
        dev.wait_until_stopped()
        print(f"Current angle: {dev.angle}°")
