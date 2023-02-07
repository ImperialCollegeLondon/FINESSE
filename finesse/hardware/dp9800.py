"""This module provides an interface to DP9800 temperature readers."""
# import logging
from typing import List

# from pubsub import pub
from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE, Serial


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
        self.data: bytes
        self.sysflag: str

        # logger: opened serial port on port (e.g.) /dev/ttyUSB0

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
        self.serial.close()

    def print_sysflag(self) -> None:
        """Print the settings of the device as stored in the system flag."""
        instr_type = ["TC", "PT"][int(self.sysflag[0])]
        logging_state = ["no logging", "logging active"][int(self.sysflag[3])]
        scanning_state = ["no scan", "autoscan active"][int(self.sysflag[5])]
        audible_state = ["silence", "audible"][int(self.sysflag[6])]
        temp_unit = ["deg C", "deg F"][int(self.sysflag[7])]
        print(f"Instrument type: {instr_type}")
        print(f"Logging: {logging_state}")
        print(f"Autoscan: {scanning_state}")
        print(f"Audible button: {audible_state}")
        print(f"Temperature unit: {temp_unit}")

    def read(self) -> None:
        """Read temperature data from the DP9800.

        The device returns a sequence of bytes corresponding to the
        temperatures measured on each channel, in the format

          STX T SP t1 SP t2 SP t3 SP t4 SP t5 SP t6 SP t7 SP t8 SP t9 ff ETX BCC

        where t1, t2, etc. are the temperature values.
        STX: Start of Text (ASCII 2)
        ETX: End of Text (ASCII 3)
        BCC: Block Check Character
        SP: Space (ASCII 32)
        ff: System flag in hexadecimal
            bit mask: [TxxLxSAF]
            F - bit 0: temperature unit: 0 = deg C, 1 = deg F
            A - bit 1: audible button:   0 = silence, 1 = audible
            S - bit 2: autoscan:         0 = no scan, 1 = autoscan active
            x - bit 3: must be 0
            L - bit 4: logging:          0 = no logging, 1 = logging active
            x - bit 5: must be 0
            x - bit 6: must be 0
            T - bit 7: instrument type:  0 = TC, 1 = PT

        Temperature values have the format
          %4.2f
        The sequence of bytes is translated into a list of ASCII strings
        representing each of the temperatures, and finally into floats.

        Note a slight peculiarity:
        The device actually returns 9 values, while the documentation
        states that there should be 8. The device shows 8 values,
        corresponding to the values with indices 1 to 8. The first value
        (at index 0) is therefore ignored.
        """
        error = 0
        # check bytes in waiting
        # if none, return error
        if self.serial.in_waiting == 0:
            error = 1
        line = self.serial.readline()
        bcc = chr(line[-2])

        # Perform checks
        assert line[0] == 2  # STX
        assert line[-3] == 3  # ETX
        assert line[-1] == 0  # NUL

        # Check BCC
        bcc_chars = self.data[1:-2]
        byte_sum = 0
        for byte in bcc_chars:
            byte_sum ^= byte

        if byte_sum != bcc:
            print("Error with BCC")
            error = 1

        if not error:
            self.data = line
            # logger: successful read from DP9800
        # else:
        # logger: unsuccessful read from DP9800

    def parse(self) -> List[float]:
        """Parse temperature data read from the DP9800.

        Returns:
            vals: A list containing the temperature values recorded by
                  the DP9800 device.
        """
        if self.data == b"":
            print("Need to read data first")
            return []
        else:
            line_ascii = self.data.decode()
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

            self.sysflag = bin(int(line_ascii[-5:-3], 16))[
                2:
            ]  # must be an easier way....

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
        val = self.serial.write(command)
        # logger: wrote to DP9800
        return val

    def write_to_log_file(self):
        """Write data to the log file."""
        print("Writing to file %s" % ("logfile"))
        print(
            "yyyyMMdd"
            + "HHmmss"
            + self.vals[1]
            + self.vals[2]
            + self.vals[3]
            + self.vals[4]
            + self.vals[5]
            + self.vals[6]
            + self.vals[7]
            + self.vals[8]
            + "totalseconds"
            + "angle"
        )


class DummyDP9800(DP9800):
    """A fake DP9800 device used to unit tests etc."""

    def __init__(self) -> None:
        """Open the connection to the device."""
        self.data: bytes
        self.sysflag: str

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
        return DummyDP9800()

    def close(self) -> None:
        """Close the connection to the device."""
        pass

    def read(self) -> None:
        """Mimic reading data from the device."""
        self.data = (
            b"\x02T   27.16   19.13   17.61   26.49  850.00"
            + b"   24.35   68.65   69.92   24.1986\x03M\x00"
        )

    def write(self, command: bytes) -> int:
        """Mimic writing data to the device."""
        return 0


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        dev = DP9800.create(sys.argv[1])
        print(dev.serial)
    else:
        dev = DummyDP9800()
    val = dev.write(b"\x04T\x05")
    print(val)
    dev.read()
    vals = dev.parse()
    print(vals)
    dev.print_sysflag()
    dev.close()
