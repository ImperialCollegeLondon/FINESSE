"""Panel and widgets related to the control of the OPUS interferometer."""
import logging
import weakref
from functools import partial
from typing import Dict, Optional

from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

COMMANDS = {
    "status": "opusrs/stat.htm",
    "connect": "opusrs/cmd.htm?opusrsconnect",
    "start": "opusrs/cmd.htm?opusrsstart",
    "stop": "opusrs/cmd.htm?opusrsstop",
    "cancel": "opusrs/cmd.htm?opusrscancel",
    "opus": "TBC",
}


class OPUSControl(QGroupBox):
    """Class that monitors and control the OPUS interferometer."""

    def __init__(self, ip: str, commands: Optional[Dict[str, str]] = None) -> None:
        """Creates the widgets to monitor and control the OPUS interferometer.

        Args:
            ip: IP for connecting to the OPUS system
            commands: Commands to use to construct the action urls
        """
        super().__init__("OPUS client view")

        self.ip = ip
        self.commands = commands if commands is not None else COMMANDS
        self.status: QWebEngineView
        self.log_hanlder: OPUSLogHandler

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QHBoxLayout:
        """Creates the controls for comunicating with the interferometer.

        Returns:
            QHBoxLayout: The layout with the buttons.
        """
        main_layout = QHBoxLayout()
        main_layout.addLayout(self._create_buttons())
        main_layout.addLayout(self._create_log_area())
        main_layout.addLayout(self._create_status_page())
        return main_layout

    def _create_buttons(self) -> QVBoxLayout:
        """Creates the buttons.

        Returns:
            QHBoxLayout: The layout with the buttons.
        """
        btn_layout = QVBoxLayout()

        button = QPushButton("Status")
        button.clicked.connect(self.display_status)  # type: ignore
        btn_layout.addWidget(button)

        for name in self.commands.keys():
            if name in ("status", "opus"):
                continue

            button = QPushButton(name.capitalize())
            button.clicked.connect(  # type: ignore
                partial(self.on_acction_button_clicked, action=name.lower())
            )
            btn_layout.addWidget(button)

        button = QPushButton("OPUS")
        button.clicked.connect(self.open_opus)  # type: ignore
        btn_layout.addWidget(button)

        btn_layout.addStretch()

        return btn_layout

    def _create_log_area(self) -> QVBoxLayout:
        """Creates the log area for OPUS-related communication.

        Returns:
            QVBoxLayout: The layout with the log area.
        """
        log_box = QGroupBox("Error log")
        log_area = QTextBrowser()
        self.log_hanlder = OPUSLogHandler.set_handler(log_area)

        _layout = QVBoxLayout()
        _layout.addWidget(log_area)
        log_box.setLayout(_layout)

        layout = QVBoxLayout()
        layout.addWidget(log_box)
        return layout

    def _create_status_page(self) -> QVBoxLayout:
        """Creates the status_page.

        Returns:
            QHBoxLayout: The layout with the web view.
        """
        status_page = QGroupBox("Status")
        self.status = QWebEngineView()
        self.status.setMinimumSize(QSize(200, 200))

        _layout = QVBoxLayout()
        _layout.addWidget(self.status)
        status_page.setLayout(_layout)

        layout = QVBoxLayout()
        layout.addWidget(status_page)
        return layout

    def url(self, action: str) -> str:
        """Builds an URL out of the ip and the action.

        Args:
            action: The action to use.

        Returns:
            str: The constructed URL
        """
        return f"http://{self.ip}/{self.commands[action]}"

    def on_acction_button_clicked(self, action: str) -> None:
        """Execute the given action by sending a message to the appropriate topic.

        TODO: Here assuming we are going to use pubsub or equivalent to send messages
        around and communicate between backend and front end.

        Args:
            action: Action to be executed.
        """
        logging.info(f"OPUS action '{self.url(action)}' executed!")

    def display_status(self) -> None:
        """Retrieves and displays the new status.

        TODO: I'm not sure who should populate the error log in the GUI. Probably the
        ones handling the individual actions above. These are all placeholders, for now.
        """
        logging.info("Getting OPUS status!")
        self.status.load(QUrl(self.url("status")))
        self.status.show()

        logging.getLogger("OPUS").error("Oh, no! Something bad happened!")

    def open_opus(self) -> None:
        """Opens OPUS front end somewhere else.

        TODO: No idea what this is supposed to do.
        """
        logging.info("Going to OPUS!")


class OPUSLogHandler(logging.Handler):
    """Specific logger for the errors related to OPUS.

    Only log messages using the OPUS logger will be recorded here. Typically, they will
    be error messages, but it can be any information worth to be logged.
    """

    @classmethod
    def set_handler(cls, log_area: QTextBrowser):
        """Creates the handler and adds it to the logger.

        Args:
            log_area: The area where the log will be printed.
        """
        ch = cls(weakref.ref(log_area))

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s]: %(message)s", datefmt="%Y/%m/%d %H:%M:%S"
        )
        ch.setFormatter(formatter)

        logging.getLogger("OPUS").addHandler(ch)

    def __init__(self, log_area: weakref.ref):
        """Constructor of the Handler.

        Args:
            log_area: A weak reference to the log area.
        """
        super(OPUSLogHandler, self).__init__()
        self.log_area = log_area

    def emit(self, record):
        """Add the record to the text area.

        If the log area has been destroyed before the logger, it will raise an
        AttributeError. This can only happen during tests and can be safely ignored.
        """
        try:
            self.log_area().append(self.format(record))
            cursor = self.log_area().textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_area().setTextCursor(cursor)
        except AttributeError:
            pass


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    opus = OPUSControl("127.0.0.1", commands=COMMANDS)
    window.setCentralWidget(opus)
    window.show()
    app.exec()
