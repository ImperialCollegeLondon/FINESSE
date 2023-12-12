"""Tests for the DevicePanel."""
from collections.abc import Sequence
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pytestqt.qtbot import QtBot

from finesse.gui.device_panel import DevicePanel


class _ChildDevicePanel(DevicePanel):
    """Inherit from DevicePanel in order to test __init_subclass__."""

    def __init__(self) -> None:
        super().__init__("my_device", "My Panel")

        # Add some extra widgets
        layout = QVBoxLayout()
        for _ in range(2):
            layout.addWidget(QWidget())
        self.setLayout(layout)


@pytest.fixture
def panel(qtbot: QtBot) -> DevicePanel:
    """A fixture providing a DevicePanel."""
    return _ChildDevicePanel()


def _check_controls_enabled(panel: DevicePanel, enabled: bool) -> None:
    widgets: Sequence[QWidget] = panel.findChildren(QWidget)

    assert widgets  # no point in doing the test unless there's at least one widget!

    assert all(widget.isEnabled() == enabled for widget in widgets)


def test_init(subscribe_mock: MagicMock, qtbot: QtBot) -> None:
    """Test DevicePanel's constructor."""
    panel = DevicePanel("my_device", "My Title")

    subscribe_mock.assert_any_call(panel._on_device_opened, "device.opened.my_device")
    subscribe_mock.assert_any_call(panel._on_device_closed, "device.closed.my_device")


def test_set_controls_enabled(panel: DevicePanel) -> None:
    """Test the set_controls_enabled() method."""
    # The controls should start off disabled
    _check_controls_enabled(panel, False)

    # Re-enable them
    panel.set_controls_enabled(True)
    _check_controls_enabled(panel, True)

    # Disable them again
    panel.set_controls_enabled(False)
    _check_controls_enabled(panel, False)


def test_on_device_opened(panel: DevicePanel) -> None:
    """Test the _on_device_opened() method."""
    with patch.object(panel, "set_controls_enabled") as enable_mock:
        panel._on_device_opened()
        enable_mock.assert_called_once_with(True)


def test_on_device_closed(panel: DevicePanel) -> None:
    """Test the _on_device_closed() method."""
    with patch.object(panel, "set_controls_enabled") as enable_mock:
        panel._on_device_closed(MagicMock())
        enable_mock.assert_called_once_with(False)
