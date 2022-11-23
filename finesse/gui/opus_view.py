"""Panel and widgets related to the control of the OPUS interferometer."""
import logging
from functools import partial

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QVBoxLayout


class OPUSControl(QGroupBox):
    """Class that monitors and control the OPUS interferometer."""

    _btn_actions = ("Status", "Cancel", "Start", "Stop", "Connect", "OPUS")

    def __init__(self) -> None:
        """Creates the widgets to monitor and control the OPUS interferometer."""
        super().__init__("OPUS client view")

        layout = self._create_controls()
        self.setLayout(layout)

    def _create_controls(self) -> QHBoxLayout:
        """Creates the controls for the ports of the devices.

        Returns:
            QHBoxLayout: The layout with the widgets.
        """
        layout = QVBoxLayout()
        for action in self._btn_actions:

            button = QPushButton(action)
            button.released.connect(  # type: ignore
                partial(self.on_button_clicked, action=action)
            )
            layout.addWidget(button)

        main_layout = QHBoxLayout()
        main_layout.addLayout(layout)

        return main_layout

    def on_button_clicked(self, action: str) -> None:
        """Execute the given action by sending a message to the appropriate topic.

        TODO: Here assuming we are going to use pubsub or equivalent to send messages
        around and communicate between backend and front end.

        Args:
            action: Action to be executed.
        """
        logging.info(f"Action '{action}' executed!")


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)

    window = QMainWindow()
    opus = OPUSControl()
    window.setCentralWidget(opus)
    window.show()
    app.exec()
