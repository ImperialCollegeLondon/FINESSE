"""The HardwareSet dataclass and associated helper functions."""
from __future__ import annotations

import bisect
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from frozendict import frozendict
from pubsub import pub
from PySide6.QtCore import QFile
from PySide6.QtWidgets import QMessageBox
from schema import And, Optional, Schema

from finesse.config import HARDWARE_SET_USER_PATH
from finesse.device_info import DeviceInstanceRef
from finesse.gui.error_message import show_error_message
from finesse.gui.hardware_set.device_connection import close_device, open_device


@dataclass(frozen=True)
class OpenDeviceArgs:
    """Arguments needed to open a device."""

    instance: DeviceInstanceRef
    class_name: str
    params: frozendict[str, Any] = field(default_factory=frozendict)

    def open(self) -> None:
        """Open the device."""
        open_device(self.class_name, self.instance, self.params)

    def close(self) -> None:
        """Close the device."""
        close_device(self.instance)

    @classmethod
    def create(
        cls, instance: str, class_name: str, params: Mapping[str, Any] = frozendict()
    ) -> OpenDeviceArgs:
        """Create an OpenDeviceArgs using basic types."""
        return cls(DeviceInstanceRef.from_str(instance), class_name, frozendict(params))


def _device_to_plain_data(device: OpenDeviceArgs) -> tuple[str, dict[str, Any]]:
    """Get a representation of the device using basic data types.

    Used for serialisation.
    """
    out_dict: dict[str, Any] = dict(class_name=device.class_name)

    # Only add params key if there are parameters
    if device.params:
        out_dict["params"] = dict(device.params)

    return str(device.instance), out_dict


class HardwareSetLoadError(Exception):
    """An exception raised when one or more hardware sets fails to load."""

    def __init__(self, file_paths: Sequence[Path]) -> None:
        """Create a new HardwareSetLoadError.

        Args:
            file_paths: The paths of files which failed to load
        """
        super().__init__(
            f"Failed to load the following files: {', '.join(map(str, file_paths))}"
        )
        self.file_paths = file_paths


def _non_empty(x: Any) -> bool:
    return bool(x)


_hw_set_schema = Schema(
    {
        "name": str,
        "devices": And(
            _non_empty,
            {
                str: {
                    "class_name": str,
                    Optional("params"): And(_non_empty, dict[str, Any]),
                }
            },
        ),
    }
)
"""Schema for validating hardware set config files."""


@dataclass(frozen=True)
class HardwareSet:
    """Represents a collection of devices for a particular hardware configuration."""

    name: str
    devices: frozenset[OpenDeviceArgs]
    file_path: Path
    built_in: bool

    def __lt__(self, other: HardwareSet) -> bool:
        """For comparing HardwareSets."""
        return (not self.built_in, self.name, self.file_path) < (
            not other.built_in,
            other.name,
            other.file_path,
        )

    def save(self, file_path: Path) -> None:
        """Save this hardware set as a YAML file."""
        with file_path.open("w") as file:
            devices = dict(map(_device_to_plain_data, self.devices))
            data = dict(name=self.name, devices=devices)
            yaml.dump(data, file, sort_keys=False)

    @classmethod
    def load(cls, file_path: Path, built_in: bool = False) -> HardwareSet:
        """Load a HardwareSet from a YAML file."""
        logging.info(f"Loading hardware set from {file_path}")

        with file_path.open() as file:
            plain_data: dict[str, Any] = yaml.safe_load(file)

        # Check that loaded data matches schema
        _hw_set_schema.validate(plain_data)

        devices = frozenset(
            OpenDeviceArgs.create(k, **v)
            for k, v in plain_data.get("devices", {}).items()
        )
        return cls(plain_data["name"], devices, file_path, built_in)


def _get_new_hardware_set_path(
    stem: str, output_dir: Path = HARDWARE_SET_USER_PATH
) -> Path:
    """Get a new valid path for a hardware set.

    If the containing directory does not exist, it will be created.

    Args:
        stem: The root of the filename, minus the extension
        output_dir: The output directory
    """
    file_name = f"{stem}.yaml"
    file_path = output_dir / file_name
    i = 2
    while file_path.exists():
        file_name = f"{stem}_{i}.yaml"
        file_path = output_dir / file_name
        i += 1

    output_dir.mkdir(exist_ok=True)
    return file_path


def _save_hardware_set(hw_set: HardwareSet) -> None:
    """Save a hardware set to disk and add to in-memory store."""
    file_path = _get_new_hardware_set_path(hw_set.file_path.stem)
    logging.info(f"Copying hardware set from {hw_set.file_path} to {file_path}")
    try:
        hw_set.save(file_path)
    except Exception as error:
        show_error_message(
            None, f"Error saving file to {file_path}: {error!s}", "Could not save file"
        )
    else:
        # We need to create a new object because the file path has changed
        new_hw_set = HardwareSet(hw_set.name, hw_set.devices, file_path, built_in=False)

        # Insert into store, keeping it sorted
        bisect.insort(_hw_sets, new_hw_set)

        # Signal that a new hardware set has been added
        pub.sendMessage("hardware_set.added", hw_set=new_hw_set)


def _load_hardware_sets(dir: Path, built_in: bool) -> Iterable[HardwareSet]:
    """Load hardware sets from the specified directory.

    Raises:
        HardwareSetLoadError: If one or more files failed to load
    """
    failed_files: list[Path] = []
    for path in dir.glob("*.yaml"):
        try:
            yield HardwareSet.load(path, built_in=built_in)
        except Exception as error:
            logging.error(f"Could not load file {path}: {error!s}")
            failed_files.append(path)

    # Only raise an error after yielding as many HardwareSets as will load
    if failed_files:
        raise HardwareSetLoadError(failed_files)


def _load_builtin_hardware_sets() -> Iterable[HardwareSet]:
    """Load all the default hardware sets included with FINESSE."""
    pkg_path = str(resources.files("finesse.gui.hardware_set").joinpath())

    # In theory, this may raise an error, but let's assume that all the built-in configs
    # are in the correct format
    yield from _load_hardware_sets(Path(pkg_path), built_in=True)


def _load_user_hardware_sets() -> Iterable[HardwareSet]:
    """Load hardware sets added by the user."""
    try:
        yield from _load_hardware_sets(HARDWARE_SET_USER_PATH, built_in=False)
    except HardwareSetLoadError as error:
        # Give the user the option of deleting malformed files
        joined_paths = "\n - ".join(path.name for path in error.file_paths)
        msg_box = QMessageBox(
            QMessageBox.Icon.Critical,
            "Failed to load hardware sets",
            f"Failed to load the following hardware sets:\n\n - {joined_paths}\n\n"
            "Would you like to move them to the recycle bin?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        ret = msg_box.exec()
        if ret != QMessageBox.StandardButton.Ok:
            return

        for path in error.file_paths:
            if QFile.moveToTrash(str(path)):
                logging.info(f"Trashed {path}")
            else:
                logging.error(f"Failed to trash {path}")


def _load_all_hardware_sets() -> None:
    """Load all known hardware sets from disk."""
    global _hw_sets
    _hw_sets.extend(_load_builtin_hardware_sets())
    _hw_sets.extend(_load_user_hardware_sets())
    _hw_sets.sort()


def get_hardware_sets() -> Iterable[HardwareSet]:
    """Get all hardware sets in the store, sorted.

    This function is a generator as we do not want to expose the underlying list, which
    should only be modified in this module.

    The hardware sets are loaded lazily on the first call to this function. The reason
    for not automatically loading them when the module is imported is so that we can
    display an error dialog if it fails, for which we need a running QApplication.
    """
    if not _hw_sets:
        _load_all_hardware_sets()

    yield from _hw_sets


_hw_sets: list[HardwareSet] = []

pub.subscribe(_save_hardware_set, "hardware_set.add")
