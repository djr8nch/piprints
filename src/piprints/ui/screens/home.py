"""Touch-first idle presentation for the PiPrints booth."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class HomeScreen(QWidget):
    """Present the single session-start action while the booth is idle.

    The screen receives an application-level callable rather than a controller
    or hardware dependency. This keeps it limited to presenting intent.
    """

    def __init__(self, show_layout_selection: Callable[[], None]) -> None:
        super().__init__()
        self._show_layout_selection = show_layout_selection

        self._title_label = QLabel("PiPrints")
        self._title_label.setObjectName("homeTitle")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet("font-size: 44px; font-weight: bold;")

        self._instruction_label = QLabel("Tap Start to choose your photo layout")
        self._instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._instruction_label.setWordWrap(True)
        self._instruction_label.setStyleSheet("font-size: 20px;")

        self._start_button = QPushButton("Start")
        self._start_button.setObjectName("startButton")
        self._start_button.setMinimumSize(360, 104)
        self._start_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._start_button.setStyleSheet(
            "QPushButton { font-size: 32px; font-weight: bold; padding: 16px 48px; }"
            "QPushButton:pressed { background-color: #b8b8b8; }"
            "QPushButton:disabled { color: #777777; background-color: #dddddd; }"
        )
        self._start_button.clicked.connect(self._request_session_start)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(20)
        layout.addStretch(2)
        layout.addWidget(self._title_label)
        layout.addWidget(self._instruction_label)
        layout.addSpacing(16)
        layout.addWidget(self._start_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(3)

    def reset_presentation(self) -> None:
        """Restore the idle action after a workflow returns to the home screen."""
        self._start_button.setEnabled(True)
        self._start_button.clearFocus()

    def _request_session_start(self) -> None:
        """Open layout selection through the presentation flow."""
        self._start_button.setEnabled(False)
        self._show_layout_selection()
