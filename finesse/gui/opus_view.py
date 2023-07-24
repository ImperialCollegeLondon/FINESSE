"""Panel and widgets related to the control of the OPUS interferometer."""
import logging
import weakref
from functools import partial

from pubsub import pub
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)

from ..em27_status import EM27Status


class OPUSControl(QGroupBox):
    """Class that monitors and controls the OPUS interferometer."""

    COMMANDS = ["status", "cancel", "stop", "start", "connect"]
    """The default commands shown for interacting with OPUS."""

    def __init__(self, commands: list[str] = COMMANDS) -> None:
        """Create the widgets to monitor and control the OPUS interferometer."""
        super().__init__("OPUS client view")

        self.commands = commands
        self.logger = logging.getLogger("OPUS")

        layout = self._create_controls()
        self.setLayout(layout)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.MinimumExpanding,
        )

        pub.subscribe(self._log_request, "opus.request")
        pub.subscribe(self._log_response, "opus.response")
        pub.subscribe(self._log_error, "opus.error")

    def _create_controls(self) -> QHBoxLayout:
        """Creates the controls for communicating with the interferometer.

        Returns:
            The layout with the buttons
        """
        main_layout = QHBoxLayout()
        main_layout.addWidget(self._create_log_area())
        main_layout.addLayout(self._create_buttons())
        return main_layout

    def _create_buttons(self) -> QVBoxLayout:
        """Creates the buttons.

        Returns:
            The layout with the buttons
        """
        btn_layout = QVBoxLayout()

        for name in self.commands:
            button = QPushButton(name.capitalize())
            button.clicked.connect(
                partial(self.on_command_button_clicked, command=name.lower())
            )
            btn_layout.addWidget(button)

        button = QPushButton("OPUS")
        button.clicked.connect(self.open_opus)
        btn_layout.addWidget(button)

        btn_layout.addStretch()

        return btn_layout

    def _create_log_area(self) -> QGroupBox:
        """Creates the log area for OPUS-related communication.

        Returns:
            Widget containing the log area
        """
        log_box = QGroupBox("Error log")
        log_area = QTextBrowser()
        OPUSLogHandler.set_handler(self.logger, log_area)

        log_layout = QVBoxLayout()
        log_layout.addWidget(log_area)
        log_box.setLayout(log_layout)

        return log_box

    def _log_request(self, command: str) -> None:
        """Log when a command request is sent."""
        self.logger.info(f'Executing command "{command}"')

    def _log_response(
        self,
        status: EM27Status,
        text: str,
        error: tuple[int, str] | None,
    ) -> None:
        self.logger.info(f"Response ({status.value}): {text}")
        if error:
            self.logger.error(f"Error ({error[0]}): {error[1]}")

    def _log_error(self, error: BaseException) -> None:
        self.logger.error(f"Error during request: {str(error)}")

    def on_command_button_clicked(self, command: str) -> None:
        """Execute the given command by sending a message to the appropriate topic.

        Args:
            command: OPUS command to be executed
        """
        pub.sendMessage("opus.request", command=command)

    def _request_status(self) -> None:
        self.logger.info("Requesting status")
        pub.sendMessage("opus.request", command="status")

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
