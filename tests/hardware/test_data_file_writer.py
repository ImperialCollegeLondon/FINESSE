"""Tests for the DataFileWriter class."""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from finesse.config import TEMPERATURE_MONITOR_TOPIC
from finesse.hardware.data_file_writer import DataFileWriter, _get_metadata


@pytest.fixture
def writer() -> DataFileWriter:
    """A fixture providing a DataFileWriter."""
    return DataFileWriter()


def test_init(subscribe_mock: MagicMock) -> None:
    """Test DataFileWriter's constructor."""
    writer = DataFileWriter()
    subscribe_mock.assert_any_call(writer.open, "data_file.open")
    subscribe_mock.assert_any_call(writer.close, "data_file.close")


@patch("finesse.hardware.data_file_writer.config.NUM_TEMPERATURE_MONITOR_CHANNELS", 2)
@patch("finesse.hardware.data_file_writer._get_metadata")
@patch("finesse.hardware.data_file_writer.Writer")
def test_open(
    csv_writer_mock: Mock,
    get_metadata_mock: Mock,
    writer: DataFileWriter,
    subscribe_mock: MagicMock,
) -> None:
    """Test the open() method."""
    header = MagicMock()
    get_metadata_mock.return_value = header
    csv_writer = MagicMock()
    csv_writer_mock.return_value = csv_writer
    path = Path("/my/path.csv")
    writer.open(path)
    csv_writer_mock.assert_called_once_with(path, header)
    assert writer._writer is csv_writer
    csv_writer.writerow.assert_called_once_with(
        ("Date", "Time", "Temp1", "Temp2", "TimeAsSeconds")
    )
    subscribe_mock.assert_any_call(
        writer.write, f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response"
    )


@patch("finesse.hardware.data_file_writer.Writer")
def test_open_error(
    csv_writer_mock: Mock,
    writer: DataFileWriter,
    sendmsg_mock: MagicMock,
    subscribe_mock: MagicMock,
) -> None:
    """Test the open() method handles errors correctly."""
    error = Exception()
    csv_writer_mock.side_effect = error
    writer.open(Path("/my/path.csv"))

    subscribe_mock.assert_not_called()
    sendmsg_mock.assert_called_once_with("data_file.error", error=error)


def test_close(writer: DataFileWriter, unsubscribe_mock: MagicMock) -> None:
    """Test the close() method."""
    writer._writer = MagicMock()
    writer.close()
    writer._writer.close.assert_called_once_with()
    unsubscribe_mock.assert_called_once_with(
        writer.write, f"serial.{TEMPERATURE_MONITOR_TOPIC}.data.response"
    )


def test_get_metadata() -> None:
    """Test _get_metadata().

    Checks that the result is convertible to YAML and that the number of lines output
    hasn't changed as users may be relying on this for parsing.
    """
    metadata = _get_metadata("FILENAME")
    serialised = str(yaml.safe_dump(metadata))
    assert serialised.count("\n") == 12


def test_write(writer: DataFileWriter) -> None:
    """Test the write() method."""
    time = datetime(2023, 4, 14, 0, 1, 0)  # one minute past midnight
    data = [Decimal(i) for i in range(3)]

    writer._writer = MagicMock()
    writer.write(time, data)
    writer._writer.writerow.assert_called_once_with(("20230414", "00:01:00", *data, 60))


def test_write_error(writer: DataFileWriter, sendmsg_mock: MagicMock) -> None:
    """Test the write() method when an error occurs."""
    time = datetime(2023, 4, 14, 0, 1, 0)  # one minute past midnight
    data = [Decimal(i) for i in range(3)]

    writer._writer = MagicMock()
    error = Exception()
    writer._writer.writerow.side_effect = error
    writer.write(time, data)
    sendmsg_mock.assert_called_once_with("data_file.error", error=error)
