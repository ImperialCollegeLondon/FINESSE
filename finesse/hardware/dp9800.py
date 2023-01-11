"""This module provides an interface to DP9800 temperature readers."""

from typing import List

from serial import EIGHTBITS, PARITY_NONE, STOPBITS_ONE, Serial


class DP9800:
    """An interface for DP9800 temperature readers."""

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

    def read(self) -> List[float]:
        """Read temperature data from the DP9800.

        The device returns a sequence of bytes corresponding to the
        temperatures measured on each channel, in the format
          STX T SP t1 SP t2 SP t3 SP t4 SP t5 SP t6 SP t7 SP t8 02 ETX BCC
        where t1, t2, etc. are the temperature values. Temperature values
        have the format
          %4.2f
        The sequence of bytes is translated into a list of ascii strings
        representing each of the temperatures, and finally into floats.

        Note a slight peculiarity:
        The device actually returns 9 values, while the documentation
        states that there should be 8. The device shows 8 values,
        corresponding to the values 2 to 9. The first value is
        therefore ignored.

        Returns:
            vals: A list containing the temperature values recorded by
                  the DP9800 device.
        """
        line = self.serial.readline()
        assert line[0] == 2
        assert line[-3] == 3
        assert line[-1] == 0
        line_ascii = line.decode()
        vals_str = [""] * (self.NUM_CHANNELS + 1)
        vals = [0.0] * (self.NUM_CHANNELS + 1)
        # stx = line[0]
        # mode = line[1]
        for i in range(self.NUM_CHANNELS + 1):
            vals_str[i] = line_ascii[
                self.NUM_CHANNELS * i + 3 : self.NUM_CHANNELS * i + 10
            ]
            vals[i] = float(vals_str[i])
        return vals[1:]

    def write(self, command: bytes) -> int:
        r"""Write a message to the DP9800.

        Likely to just be used to initiate a read operation, triggered
        with the command \x04T\x05.

        Args:
            command: The command to write to the device
        """
        val = self.serial.write(command)
        return val

    def write_to_log_file(self):
        """Write data to the log file."""
        print("Writing to file %s" % ("logfile"))
        print(
            "yyyyMMdd"
            + "HHmmss"
            + "pt100[2]"
            + "pt100[3]"
            + "pt100[4]"
            + "pt100[5]"
            + "pt100[6]"
            + "pt100[7]"
            + "pt100[8]"
            + "pt100[9]"
            + "totalseconds"
            + "angle"
        )


if __name__ == "__main__":
    import sys

    dev = DP9800.create(sys.argv[1])
    print(dev.serial)
    val = dev.write(b"\x04T\x05")
    print(val)
    vals = dev.read()
    print(vals)
    dev.serial.close()
