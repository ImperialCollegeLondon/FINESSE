"""Class for LED Icons."""
from __future__ import annotations

from importlib import resources

from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel

_img_files = resources.files("finesse.gui.images")
_poll_on_img_data = _img_files.joinpath("poll_on.png").read_bytes()
_poll_off_img_data = _img_files.joinpath("poll_off.png").read_bytes()
_alarm_on_img_data = _img_files.joinpath("alarm_on.png").read_bytes()
_alarm_off_img_data = _img_files.joinpath("alarm_off.png").read_bytes()

_poll_on_img = QImage.fromData(_poll_on_img_data)
_poll_off_img = QImage.fromData(_poll_off_img_data)
_alarm_on_img = QImage.fromData(_alarm_on_img_data)
_alarm_off_img = QImage.fromData(_alarm_off_img_data)


class LEDIcon(QLabel):
    """QLabel object to represent an LED with on/off status."""

    def __init__(self, on_img: QImage, off_img: QImage, is_on: bool = False) -> None:
        """Creates the LED icon, sets its status and stores corresponding image data.

        Args:
            on_img (QImage): QImage for LED on state.
            off_img (QImage): QImage for LED off state.
            is_on (bool): On/off status of LED.
        """
        super().__init__()
        self._on_img = on_img
        self._off_img = off_img
        if is_on:
            self._turn_on()
        else:
            self._turn_off()
        self.timer = QTimer()
        self.timer.timeout.connect(self._turn_off)  # type: ignore

    @classmethod
    def create_poll_icon(cls) -> LEDIcon:
        """Creates the LED icon for polling the server."""
        return cls(on_img=_poll_on_img, off_img=_poll_off_img)

    @classmethod
    def create_alarm_icon(cls) -> LEDIcon:
        """Creates the LED icon to indicate alarm status."""
        return cls(on_img=_alarm_on_img, off_img=_alarm_off_img)

    def _turn_on(self) -> None:
        """Turns the LED on."""
        self._is_on = True
        self.setPixmap(QPixmap(self._on_img))

    def _turn_off(self) -> None:
        """Turns the LED off."""
        self._is_on = False
        self.setPixmap(QPixmap(self._off_img))

    def flash(self, duration: int = 250) -> None:
        """Turns the LED on for a specified duration.

        Args:
            duration (int): Number of milliseconds to keep LED lit for
        """
        self._turn_on()
        self.timer.singleShot(duration, self._turn_off)
