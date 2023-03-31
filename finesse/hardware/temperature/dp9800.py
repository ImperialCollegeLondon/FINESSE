"""This module provides an interface to DP9800 temperature readers."""
import logging
from datetime import datetime
from decimal import Decimal

from pubsub import pub
from serial import Serial, SerialException

from .temperature_monitor_base import TemperatureMonitorBase


def check_data(data: bytes) -> None:
    """Perform message integrity checks.

    Check characters that we know should be constant. The message should
    start with STX, end with NUL and contain an ETX. The exact position
    of ETX is uncertain since it depends on the width of the BCC.

    Args:
        data: the message to check

    Raises:
        DP9800Error: Malformed message received from device
    """
    if data[0] != 2:  # STX
        raise DP9800Error("Start transmission character not detected")
    if data.find(3) == -1:  # ETX
        raise DP9800Error("End transmission character not detected")
    if data[-1] != 0:  # NUL
        raise DP9800Error("Null terminator not detected")


def calculate_bcc(data: bytes) -> int:
    """Calculate block check character.

    Args:
        data: the message to check

    Returns:
        bcc: block check character
    """
    bcc_chars = data[1:-2]
    bcc = 0
    for byte in bcc_chars:
        bcc ^= byte

    return bcc


def parse_data(data: bytes) -> tuple[list[Decimal], str]:
    """Parse temperature data read from the DP9800.

    The sequence of bytes is translated into a list of ASCII strings
    representing each of the temperatures, and finally into floats.

    Returns:
        vals: A list of Decimals containing the temperature values recorded
              by the DP9800 device.
        sysflag: string representation of the system flag bitmask
    """
    check_data(data)
    bcc = calculate_bcc(data)
    if bcc != data[-2]:
        raise DP9800Error("BCC check failed")

    try:
        data_ascii = data.decode("ascii")
    except UnicodeDecodeError as e:
        raise DP9800Error(e)

    vals_begin = 3  # Following STX T SP
    vals_end = 74  # Following STX T (SP %4.2f)*9, assuming 9 vals
    etx_index = data.find(b"\x03")

    vals = [Decimal(val) for val in data_ascii[vals_begin:vals_end].split()]

    sysflag = bin(int(data_ascii[vals_end:etx_index], 16))

    # Omit mysterious first temperature, and omit binary identifier characters
    return vals[1:], sysflag[2:]


class DP9800Error(Exception):
    """Indicates that an error occurred while communicating with the device."""


class DP9800(TemperatureMonitorBase):
    """An interface for DP9800 temperature readers.

    The manual for this device is available at:
    https://assets.omega.com/manuals/M5210.pdf
    """

    def __init__(self, serial: Serial) -> None:
        """Create a new DP9800 from an existing serial device.

        Args:
            serial: Serial device
        """
        super().__init__("DP9800")
        self.serial = serial

    def close(self) -> None:
        """Close the connection to the device.

        Raises:
            DP9800Error: Error communicating with device
        """
        try:
            self.serial.close()
        except SerialException as e:
            raise DP9800Error(e)
        else:
            pub.sendMessage("temperature_monitor.close")
            logging.info("Closed connection to DP9800")

    def get_device_settings(self, sysflag: str) -> dict[str, str]:
        """Provide the settings of the device as stored in the system flag.

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

        Args:
            sysflag: string representation of the system flag bitmask

        Returns:
            dictionary containing the current device settings
        """
        return {
            "instrument_type": ["TC", "PT"][int(sysflag[0])],
            "logging_state": ["no logging", "logging active"][int(sysflag[3])],
            "scanning_state": ["no scan", "autoscan active"][int(sysflag[5])],
            "audible_state": ["silence", "audible"][int(sysflag[6])],
            "temperature_unit": ["deg C", "deg F"][int(sysflag[7])],
        }

    def read(self) -> bytes:
        """Read temperature data from the DP9800.

        The DP9800 returns a sequence of bytes containing the
        temperatures measured on each channel, in the format

          STX T SP t1 SP t2 SP t3 SP t4 SP t5 SP t6 SP t7 SP t8 SP t9 ff ETX BCC NUL

        where
            t1, t2, ..., t9: temperature values in the format %4.2f
            STX: Start of Text (ASCII 2)
            ETX: End of Text (ASCII 3)
            NUL: Null character (ASCII 0)
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

        Raises:
            DP9800Error: Malformed message received from device
        """
        # require at least 4 bytes else checks will fail
        min_length = 4
        try:
            data = self.serial.read_until(b"\x00", size=min_length)
        except SerialException as e:
            raise DP9800Error(e)

        if len(data) < min_length:
            raise DP9800Error("Insufficient data read from device")

        return data

    def request_read(self) -> None:
        """Write a message to the DP9800 to prepare for a read operation.

        Format:

          EOT T ENQ

        EOT: End of Transmission (ASCII 4)
        ENQ: Enquiry (ASCII 5)

        Raises:
            DP9800Error: Error writing to the device
        """
        try:
            self.serial.write(b"\x04T\x05")
        except Exception as e:
            raise DP9800Error(e)

    def send_temperatures(self) -> None:
        """Perform the complete process of reading from the DP9800.

        Writes to the DP9800 requesting a read operation.
        Reads the raw data from the DP9800.
        Parses the data and broadcasts the temperatures.
        """
        try:
            self.request_read()
            data = self.read()
            time_now = datetime.now().timestamp()
            temperatures, _ = parse_data(data)
        except DP9800Error as e:
            self._error_occurred(e)
        else:
            pub.sendMessage(
                "temperature_monitor.data.response",
                temperatures=temperatures,
                time=time_now,
            )

    def _error_occurred(self, exception: BaseException) -> None:
        """Log and communicate that an error occurred."""
        logging.error(f"Error during DP9800 query:\t{exception}")
        pub.sendMessage("temperature_monitor.error", message=str(exception))