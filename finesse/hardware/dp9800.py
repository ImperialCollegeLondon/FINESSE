"""This module provides an interface to DP9800 temperature readers."""
import logging
from decimal import Decimal

from pubsub import pub
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE, Serial, SerialException


class DP9800Error(Exception):
    """Indicates that an error occurred while communicating with the device."""


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
        self._sysflag: str = ""

        logging.info(f"Opened connection to DP9800 on port {self.serial.port}")
        pub.sendMessage("temperature_monitor.open")
        pub.subscribe(self.send_temperatures, "temperature_monitor.data.request")

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

        return DP9800(serial, max_attempts)

    def close(self) -> None:
        """Close the connection to the device."""
        try:
            self.serial.close()
            pub.sendMessage("temperature_monitor.close")
            logging.info("Closed connection to DP9800")
        except SerialException as e:
            self._error_occurred(DP9800Error(e))

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

    def read(self) -> bytes:
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

        Returns:
            data: the sequence of bytes read from the device
        """
        num_bytes_to_read = self.serial.in_waiting
        if num_bytes_to_read == 0:
            data = b""
        else:
            try:
                data = self.serial.read(num_bytes_to_read)
            except SerialException as e:
                self._error_occurred(DP9800Error(e))

            # Perform message integrity checks
            # Check characters we know
            if data[0] != 2:  # STX
                self._error_occurred(
                    DP9800Error("Start transmission character not detected")
                )
            if data[-3] != 3:  # ETX
                self._error_occurred(
                    DP9800Error("End transmission character not detected")
                )
            if data[-1] != 0:  # NUL
                self._error_occurred(DP9800Error("Null terminator not detected"))

            # Check BCC
            bcc = data[-2]
            bcc_chars = data[1:-2]
            byte_sum = 0
            for byte in bcc_chars:
                byte_sum ^= byte

            if byte_sum != bcc:
                self._error_occurred(DP9800Error("BCC check failed"))

        logging.info(f"Read {len(data)} bytes from DP9800")
        return data

    def parse(self, data: bytes) -> list[Decimal]:
        """Parse temperature data read from the DP9800.

        The sequence of bytes is translated into a list of ASCII strings
        representing each of the temperatures, and finally into floats.

        Returns:
            vals: A list of Decimals containing the temperature values recorded
                  by the DP9800 device.
        """
        if data == b"":
            return []
        else:
            data_ascii = data.decode("ascii")
            vals_str = [""] * (self.NUM_CHANNELS + 1)
            vals = [Decimal(0.0)] * (self.NUM_CHANNELS + 1)
            offset = 3  # offset of temperature values from start of message
            width = 7  # width of temperature strings
            for i in range(self.NUM_CHANNELS + 1):
                vals_str[i] = data_ascii[
                    self.NUM_CHANNELS * i
                    + offset : self.NUM_CHANNELS * i
                    + (offset + width)
                ]
                vals[i] = Decimal(vals_str[i])

            sysflag = bin(int(data_ascii[-5:-3], 16))
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
            val: Number of bytes written to the device
        """
        num_bytes_written = self.serial.write(command)
        logging.info(f"Wrote {num_bytes_written} bytes to DP9800")
        return num_bytes_written

    def send_temperatures(self) -> None:
        """Perform the complete process of reading from the DP9800.

        Writes to the DP9800 requesting a read operation.
        Reads the raw data from the DP9800.
        Parses the data and broadcasts the temperatures.
        """
        self.write(b"\x04T\x05")
        data = self.read()
        temperatures = self.parse(data)
        pub.sendMessage("temperature_monitor.data.response", values=temperatures)

    def _error_occurred(self, exception: BaseException) -> None:
        """Log and communicate that an error occurred."""
        logging.error(f"Error during DP9800 query:\t{exception}")
        pub.sendMessage("temperature_monitor.error", message=str(exception))
