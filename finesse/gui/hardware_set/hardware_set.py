"""The HardwareSet dataclass and associated helper functions."""
from __future__ import annotations

import logging
from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from frozendict import frozendict

from finesse.device_info import DeviceInstanceRef
from finesse.gui.device_connection import close_device, open_device


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


@dataclass(frozen=True)
class HardwareSet:
    """Represents a collection of devices for a particular hardware configuration."""

    name: str
    devices: frozenset[OpenDeviceArgs]
    file_path: Path
    read_only: bool

    @classmethod
    def load(cls, file_path: Path, read_only: bool = False) -> HardwareSet:
        """Load a HardwareSet from a YAML file."""
        logging.info(f"Loading hardware set from {file_path}")

        with file_path.open() as file:
            plain_data: dict[str, Any] = yaml.safe_load(file)

        devices = frozenset(
            OpenDeviceArgs.create(k, **v)
            for k, v in plain_data.get("devices", {}).items()
        )

        return cls(plain_data["name"], devices, file_path, read_only)


def load_builtin_hardware_sets() -> Generator[HardwareSet, None, None]:
    """Load all the default hardware sets included with FINESSE."""
    pkg_path = str(resources.files("finesse.gui.hardware_set").joinpath())
    for filepath in Path(pkg_path).glob("*.yaml"):
        yield HardwareSet.load(filepath, read_only=True)
