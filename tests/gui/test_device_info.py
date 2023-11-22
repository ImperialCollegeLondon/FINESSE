"""Test functionality in device_info.py."""

import pytest

from finesse.device_info import DeviceBaseTypeInfo, DeviceInstanceRef


@pytest.mark.parametrize(
    "type_info,expected",
    (
        (
            DeviceBaseTypeInfo("type_name", "Type description", (), ()),
            [(DeviceInstanceRef("type_name"), "Type description")],
        ),
        (
            DeviceBaseTypeInfo(
                "type_name",
                "Type description",
                ("name1", "name2"),
                ("Name 1", "Name 2"),
            ),
            [
                (
                    DeviceInstanceRef("type_name", f"name{i}"),
                    f"Type description (Name {i})",
                )
                for i in range(1, 3)
            ],
        ),
    ),
)
def test_get_instances_and_descriptions(
    type_info: DeviceBaseTypeInfo, expected: list[tuple[DeviceInstanceRef, str]]
) -> None:
    """Test DeviceBaseTypeInfo's get_devices_and_descriptions() method."""
    assert list(type_info.get_instances_and_descriptions()) == expected
