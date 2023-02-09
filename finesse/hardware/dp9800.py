"""This module provides an interface to DP9800 temperature readers."""
# import logging
from typing import List

from pubsub import pub
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE, Serial, SerialException


class DP9800Error(SerialException):
    """Indicates that an error has occurred with the DP9800 comms."""


class MalformedMessageError(Exception):
    """Raised when a message received was malformed."""


class DP9800:
    """An interface for DP9800 temperature readers.

    The manual for this device is available at:
    https://assets.omega.com/manuals/M5210.pdf
    """

    NUM_CHANNELS = 8
    """The number of channels on the DP9800 device."""

    def __init__(self, serial: Serial, max_attempts: int = 3) -> None:
        """Create a new DP9800 from an existing serial device.

        Args:
            serial: Serial device
            max_attempts: Maximum number of attempts for requests
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self.serial = serial
        self.max_attempts = max_attempts
        self._data: bytes = b""
        self._sysflag: str = ""

    @staticmethod
    def create(
        port: str,
        baudrate: int = 38400,
        bytesize: int = EIGHTBITS,
        parity: str = PARITY_NONE,
        stopbits: int = STOPBITS_ONE,
        timeout: float = 2.0,
        max_attempts: int = 3,
    ) -> "DP9800":
        """Create a new DP9800.

        Args:
            port: Serial port name
            baudrate: Serial port baud rate
            bytesize: the byte size
            parity: the parity
            stopbits: the stop bits
            timeout: How long to wait for read operations (seconds)
            max_attempts: Maximum number of attempts for requests
        """
        serial = Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
        )

        # logger: opened serial port on port self.serial.port
        pub.sendMessage("dp9800_state", is_open=True)
        return DP9800(serial, max_attempts)

    def close(self) -> None:
        """Close the connection to the device."""
        self.serial.close()
        pub.sendMessage("dp9800_state", is_open=False)

    def print_sysflag(self) -> None:
        """Print the settings of the device as stored in the system flag.

        The system flag is stored as a bit mask with the format TxxLxSAF,
        where:
            F - bit 0: temperature unit: 0 = deg C, 1 = deg F
            A - bit 1: audible button:   0 = silence, 1 = audible
            S - bit 2: autoscan:         0 = no scan, 1 = autoscan active
            x - bit 3: must be 0
            L - bit 4: logging:          0 = no logging, 1 = logging active
            x - bit 5: must be 0
            x - bit 6: must be 0
            T - bit 7: instrument type:  0 = TC, 1 = PT
        """
        if self._sysflag == "":
            print("No system flag. Read from device first.")
        else:
            instr_type = ["TC", "PT"][int(self._sysflag[0])]
            logging_state = ["no logging", "logging active"][int(self._sysflag[3])]
            scanning_state = ["no scan", "autoscan active"][int(self._sysflag[5])]
            audible_state = ["silence", "audible"][int(self._sysflag[6])]
            temp_unit = ["deg C", "deg F"][int(self._sysflag[7])]
            print(f"Instrument type: {instr_type}")
            print(f"Logging: {logging_state}")
            print(f"Autoscan: {scanning_state}")
            print(f"Audible button: {audible_state}")
            print(f"Temperature unit: {temp_unit}")

    def read(self) -> None:
        """Read temperature data from the DP9800.

        The DP9800 returns a sequence of bytes containing the
        temperatures measured on each channel, in the format

          STX T SP t1 SP t2 SP t3 SP t4 SP t5 SP t6 SP t7 SP t8 SP t9 ff ETX BCC

        where
            t1, t2, ..., t9: temperature values in the format %4.2f
            STX: Start of Text (ASCII 2)
            ETX: End of Text (ASCII 3)
            SP: Space (ASCII 32)
            BCC: Block Check Character
            ff: System flag in hexadecimal

        For error checking, the BCC is calculated by performing consecutive XOR
        operations on the message and compared with the BCC received.

        Note a slight peculiarity:
        The device actually returns 9 temperatures, while the documentation
        states that there should be 8. The device shows 8 values, corresponding
        to the values with indices 1 to 8. The first value (at index 0) is
        therefore ignored.

        Raises:
            SerialException: An error occurred while reading from the device
            MalformedMessageError: The message read was malformed
        """
        error = 0
        num_bytes_to_read = self.serial.in_waiting
        if num_bytes_to_read == 0:
            print("No bytes to read")
            error = 1
        else:
            line = self.serial.read(num_bytes_to_read)
            bcc = line[-2]

        # Perform message integrity checks
        # Check characters we know
        assert line[0] == 2  # STX
        assert line[-3] == 3  # ETX
        assert line[-1] == 0  # NUL

        # Check BCC
        bcc_chars = line[1:-2]
        byte_sum = 0
        for byte in bcc_chars:
            byte_sum ^= byte

        if byte_sum != bcc:
            print("Error with BCC")
            raise MalformedMessageError("BCC check failed")
            error = 1

        if not error:
            self._data = line
            # logger: successful read from DP9800
        # else:
        # logger: unsuccessful read from DP9800

    def parse(self) -> List[float]:
        """Parse temperature data read from the DP9800.

        The sequence of bytes is translated into a list of ASCII strings
        representing each of the temperatures, and finally into floats.

        Returns:
            vals: A list containing the temperature values recorded by
                  the DP9800 device.
        """
        if self._data == b"":
            print("No data")
            return []
        else:
            line_ascii = self._data.decode("ascii")
            vals_str = [""] * (self.NUM_CHANNELS + 1)
            vals = [0.0] * (self.NUM_CHANNELS + 1)
            offset = 3  # offset of temperature values from start of message
            width = 7  # width of temperature strings
            for i in range(self.NUM_CHANNELS + 1):
                vals_str[i] = line_ascii[
                    self.NUM_CHANNELS * i
                    + offset : self.NUM_CHANNELS * i
                    + (offset + width)
                ]
                vals[i] = float(vals_str[i])

            sysflag = bin(int(line_ascii[-5:-3], 16))
            self._sysflag = sysflag[2:]

        return vals[1:]

    def write(self, command: bytes) -> int:
        r"""Write a message to the DP9800.

        Format:

          EOT T ENQ

        EOT: End of Transmission (ASCII 4)
        ENQ: Enquiry (ASCII 5)

        Likely to just be used to initiate a read operation, triggered
        with the command \x04T\x05.

        Args:
            command: The command to write to the device

        Returns:
            val: Result of write to device (necessary?)
        """
        num_bytes_written = self.serial.write(command)
        # logger: wrote num_bytes_written to DP9800
        return num_bytes_written

    def get_temperatures(self) -> None:
        """Perform the complete process of reading from the DP9800.

        Writes to the DP9800 requesting a read operation.
        Reads the raw data from the DP9800.
        Parses the data and broadcasts the temperatures.
        """
        self.write(b"\x04T\x05")
        self.read()
        temperatures = self.parse()
        pub.sendMessage("dp9800_data", values=temperatures)


class DummyDP9800(DP9800):
    """A fake DP9800 device used for unit tests etc."""

    def __init__(self) -> None:
        """Open the connection to the device."""
        self.in_waiting: int = 0
        self._data: bytes = b""
        self._sysflag: str = ""

    @staticmethod
    def create(
        port: str = "",
        baudrate: int = 38400,
        bytesize: int = EIGHTBITS,
        parity: str = PARITY_NONE,
        stopbits: int = STOPBITS_ONE,
        timeout: float = 2.0,
        max_attempts: int = 3,
    ) -> "DummyDP9800":
        """Create the device."""
        pub.sendMessage("dp9800_state", is_open=True)
        return DummyDP9800()

    def close(self) -> None:
        """Close the connection to the device."""
        pub.sendMessage("dp9800_state", is_open=False)

    def read(self) -> None:
        """Mimic reading data from the device."""
        error = 0
        num_bytes_to_read = self.in_waiting
        if num_bytes_to_read == 0:
            print("No bytes to read")
            error = 1
        else:
            line = (
                b"\x02T   27.16   19.13   17.61   26.49  850.00"
                + b"   24.35   68.65   69.92   24.1986\x03M\x00"
            )
            bcc = line[-2]

        # Perform message integrity checks
        # Check characters we know
        assert line[0] == 2  # STX
        assert line[-3] == 3  # ETX
        assert line[-1] == 0  # NUL

        # Check BCC
        bcc_chars = line[1:-2]
        byte_sum = 0
        for byte in bcc_chars:
            byte_sum ^= byte

        if byte_sum != bcc:
            print("Error with BCC")
            raise MalformedMessageError("BCC check failed")
            error = 1

        if not error:
            self._data = line
            # logger: successful read from DP9800
        # else:
        # logger: unsuccessful read from DP9800

        self.in_waiting = 0

    def write(self, command: bytes) -> int:
        """Pretend to write data to the device.

        Returns:
            0: indicates successful write to the device
        """
        self.in_waiting = 79
        return 0


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        dev = DP9800.create(sys.argv[1])
    else:
        dev = DummyDP9800()

    dev.get_temperatures()
    dev.close()
