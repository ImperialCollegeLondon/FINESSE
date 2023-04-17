"""Contains a panel which enables/disables child controls when device opens/closes."""
from typing import Any

from decorator import decorator
from pubsub import pub
from PySide6.QtWidgets import QGroupBox, QWidget


class SerialDevicePanel(QGroupBox):
    """A QGroupBox which enables/disables child controls when device opens/closes."""

    def __init_subclass__(cls, **kwargs):
        """Disable controls after construction."""
        super().__init_subclass__(**kwargs)

        @decorator
        def init_decorator(previous_init, self, *args, **kwargs):
            previous_init(self, *args, **kwargs)
            self.set_controls_enabled(False)

        cls.__init__ = init_decorator(cls.__init__)

    def __init__(self, name: str, title: str, *args: Any, **kwargs: Any) -> None:
        """Create a new SerialDevicePanel.

        The controls will be disabled initially.

        Args:
            name: The name of the device as used in pubsub messages
            title: The title for the underlying QGroupBox
            args: Extra arguments for the QGroupBox constructor
            kwargs: Extra keyword arguments for the QGroupBox constructor
        """
        super().__init__(title, *args, **kwargs)

        # Enable/disable controls on device connect/disconnect
        pub.subscribe(self._on_device_opened, f"serial.{name}.opened")
        pub.subscribe(self._on_device_closed, f"serial.{name}.close")

    def _on_device_opened(self) -> None:
        self.set_controls_enabled(True)

    def _on_device_closed(self) -> None:
        self.set_controls_enabled(False)

    def set_controls_enabled(self, enabled: bool) -> None:
        """Enable/disable the controls in this panel.

        Args:
            enabled: Whether to enable or disable the controls
        """
        for widget in self.findChildren(QWidget):
            widget.setEnabled(enabled)
