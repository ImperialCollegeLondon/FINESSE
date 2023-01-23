"""Panel and widgets related to the control of the OPUS interferometer."""
import logging
import weakref
from functools import partial
from typing import Optional

from pubsub import pub
from PySide6.QtCore import QSize
from PySide6.QtGui import QTextCursor
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

COMMANDS = ["cancel", "stop", "start", "connect"]
"""The default commands shown for interacting with OPUS."""


class OPUSControl(QGroupBox):
    """Class that monitors and control the OPUS interferometer."""

    def __init__(self, commands: Optional[list[str]] = None) -> None:
        """Create the widgets to monitor and control the OPUS interferometer.

        Args:
            commands: OPUS commands to use
        """
        super().__init__("OPUS client view")

        self.commands = commands if commands is not None else COMMANDS
        self.status: QWebEngineView
        self.logger = logging.getLogger("OPUS")

        layout = self._create_controls()
        self.setLayout(layout)

        pub.subscribe(self._log_response, "opus.command.response")
        pub.subscribe(self._log_response, "opus.status.response")
        pub.subscribe(self._display_status, "opus.status.response")
        pub.subscribe(self._log_error, "opus.error")

    def _create_controls(self) -> QHBoxLayout:
        """Creates the controls for communicating with the interferometer.

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
        button.clicked.connect(self._request_status)  # type: ignore
        btn_layout.addWidget(button)

        for name in self.commands:
            button = QPushButton(name.capitalize())
            button.clicked.connect(  # type: ignore
                partial(self.on_command_button_clicked, command=name.lower())
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
        OPUSLogHandler.set_handler(self.logger, log_area)

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

    def _log_response(
        self,
        status: int,
        text: str,
        error: Optional[tuple[int, str]],
        url: str,
    ) -> None:
        self.logger.info(f"Response ({status}): {text}")
        if error:
            self.logger.error(f"Error ({error[0]}): {error[1]}")

    def _log_error(self, message: str) -> None:
        self.logger.error(f"Error during request: {message}")

    def on_command_button_clicked(self, command: str) -> None:
        """Execute the given command by sending a message to the appropriate topic.

        Args:
            command: OPUS command to be executed
        """
        self.logger.info(f'Executing command "{command}"')
        pub.sendMessage("opus.command.request", command=command)

    def _request_status(self) -> None:
        self.logger.info("Requesting status")
        pub.sendMessage("opus.status.request")

    def _display_status(
        self, status: int, text: str, error: Optional[tuple[int, str]], url: str
    ) -> None:
        """Display the status in the GUI's browser pane.

        This method is a handler for the opus.status.response message, which means that
        we only reload the page displayed in self.status once the status has already
        been requested! However, the self.status widget is not really necessary (the
        user doesn't need to know how the returned HTML looks), so hopefully we can
        remove it soon, along with this hack.
        """
        self.status.load(url)
        self.status.show()

    def open_opus(self) -> None:
        """Opens OPUS front end somewhere else.

        TODO: No idea what this is supposed to do.
        """
        logging.info("Going to OPUS!")


class OPUSLogHandler(logging.Handler):
    """Specific logger for the errors related to OPUS.

    Only log messages using the OPUS logger will be recorded here. Typically, they will
    be error messages, but it can be any information worth logging.
    """

    @classmethod
    def set_handler(cls, logger: logging.Logger, log_area: QTextBrowser):
        """Creates the handler and adds it to the logger.

        Args:
            logger: The logger to set the formatter for
            log_area: The area where the log will be printed.
        """
        ch = cls(weakref.ref(log_area))

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s]: %(message)s", datefmt="%Y/%m/%d %H:%M:%S"
        )
        ch.setFormatter(formatter)

        logger.addHandler(ch)

    def __init__(self, log_area: weakref.ref):
        """Constructor of the Handler.

        Args:
            log_area: A weak reference to the log area.
        """
        super().__init__()
        self.log_area = log_area

    def emit(self, record):
        """Add the record to the text area.

        If the log area has been destroyed before the logger, it will raise an
        AttributeError. This can only happen during tests and can be safely ignored.
        """
        log_area = self.log_area()
        if not log_area:
            # log_area no longer exists
            return

        log_area.append(self.format(record))
        cursor = log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        log_area.setTextCursor(cursor)


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    opus = OPUSControl()
    window.setCentralWidget(opus)
    window.show()
    app.exec()
