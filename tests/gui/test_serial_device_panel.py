"""Tests for the SerialDevicePanel."""
from typing import Sequence
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pytestqt.qtbot import QtBot

from finesse.gui.serial_device_panel import SerialDevicePanel


class _ChildSerialDevicePanel(SerialDevicePanel):
    """Inherit from SerialDevicePanel in order to test __init_subclass__."""

    def __init__(self) -> None:
        super().__init__("my_device", "My Panel")

        # Add some extra widgets
        layout = QVBoxLayout()
        for _ in range(2):
            layout.addWidget(QWidget())
        self.setLayout(layout)


@pytest.fixture
def panel(qtbot: QtBot) -> SerialDevicePanel:
    """A fixture providing a SerialDevicePanel."""
    return _ChildSerialDevicePanel()


def _check_controls_enabled(panel: SerialDevicePanel, enabled: bool) -> None:
    widgets: Sequence[QWidget] = panel.findChildren(QWidget)

    assert widgets  # no point in doing the test unless there's at least one widget!

    assert all(widget.isEnabled() == enabled for widget in widgets)


def test_init(subscribe_mock: MagicMock, qtbot: QtBot) -> None:
    """Test SerialDevicePanel's constructor."""
    panel = SerialDevicePanel("my_device", "My Title")

    subscribe_mock.assert_any_call(panel._on_device_opened, "serial.my_device.opened")
    subscribe_mock.assert_any_call(panel.disable_controls, "serial.my_device.close")


def test_enable_controls(panel: SerialDevicePanel) -> None:
    """Test the enable_controls() method."""
    # The controls should start off disabled
    _check_controls_enabled(panel, False)

    # Re-enable them
    panel.enable_controls()
    _check_controls_enabled(panel, True)


def test_disable_controls(panel: SerialDevicePanel) -> None:
    """Test the disable_controls() method."""
    # Enable controls
    panel.enable_controls()
    _check_controls_enabled(panel, True)

    # Disable them
    panel.disable_controls()
    _check_controls_enabled(panel, False)
