"""Class for LED Icons."""
from importlib import resources

from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel

img_files = resources.files("finesse.gui.images")
poll_on_img_data = img_files.joinpath("poll_on.png").read_bytes()
poll_off_img_data = img_files.joinpath("poll_off.png").read_bytes()
alarm_on_img_data = img_files.joinpath("alarm_on.png").read_bytes()
alarm_off_img_data = img_files.joinpath("alarm_off.png").read_bytes()

poll_on_img = QImage.fromData(poll_on_img_data)
poll_off_img = QImage.fromData(poll_off_img_data)
alarm_on_img = QImage.fromData(alarm_on_img_data)
alarm_off_img = QImage.fromData(alarm_off_img_data)


class LEDIcon(QLabel):
    """QLabel object to represent an LED with on/off status."""

    def __init__(self, status: int) -> None:
        """Creates the LED icon, sets its status and stores corresponding image data."""
        super().__init__()
        self._status = status
        self._on_img = QImage()
        self._off_img = QImage()
        self._timer = QTimer()
        self._timer.timeout.connect(self._turn_off)  # type: ignore

    def _turn_on(self):
        """Turns the LED on."""
        self._status = 1
        self.setPixmap(QPixmap(self._on_img))

    def _turn_off(self):
        """Turns the LED off."""
        self._status = 0
        self.setPixmap(QPixmap(self._off_img))

    def _flash(self, duration: int = 1000):
        """Turns the LED on for a specified duration.

        Args:
            duration (int): Number of milliseconds to keep LED lit for
        """
        self._turn_on()
        self._timer.singleShot(duration, self._turn_off)


class PollIcon(LEDIcon):
    """QLabel object to represent an LED for polling server."""

    def __init__(self, status: int) -> None:
        """Creates the LED icon, sets its status and stores corresponding image data.

        Args:
            status (int): On/off status of LED. 0 = off, !0 = on
        """
        super().__init__(status=status)
        self._on_img = poll_on_img
        self._off_img = poll_off_img
        if status:
            self._turn_on()
        else:
            self._turn_off()


class AlarmIcon(LEDIcon):
    """QLabel object to represent an LED to indicate alarm status."""

    def __init__(self, status: int) -> None:
        """Creates the LED icon, sets its status and stores corresponding image data.

        Args:
            status (int): On/off status of LED. 0 = off, !0 = on
        """
        super().__init__(status=status)
        self._on_img = alarm_on_img
        self._off_img = alarm_off_img
        if status:
            self._turn_on()
        else:
            self._turn_off()
