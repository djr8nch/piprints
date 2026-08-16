"""Simple recovery presentation for application-level booth failures."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from piprints.booth import BoothErrorCategory, BoothEvent


class ErrorScreen(QWidget):
    """Show a user-friendly error and provide a route back to idle."""

    def __init__(self, reset_session: Callable[[], None]) -> None:
        super().__init__()
        self._reset_session = reset_session
        self._title_label = QLabel("Something went wrong")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPixelSize(36)
        title_font.setWeight(QFont.Weight.DemiBold)
        self._title_label.setFont(title_font)
        self._message_label = QLabel("Please return to start and try again.")
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_font = QFont()
        message_font.setPixelSize(22)
        self._message_label.setFont(message_font)

        self._retry_button = QPushButton("Try again")
        self._retry_button.setMinimumSize(280, 88)
        self._retry_button.clicked.connect(self._reset_session)
        self._return_button = QPushButton("Return to start")
        self._return_button.setMinimumSize(280, 88)
        self._return_button.clicked.connect(self._reset_session)

        actions = QHBoxLayout()
        actions.setSpacing(20)
        actions.addWidget(self._retry_button)
        actions.addWidget(self._return_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 48, 64, 48)
        layout.setSpacing(32)
        layout.addStretch()
        layout.addWidget(self._title_label)
        layout.addWidget(self._message_label)
        layout.addLayout(actions)
        layout.addStretch()

        self.setStyleSheet("background-color: #151515; color: white;")

    def show_error(self, event: BoothEvent) -> None:
        """Present application-supplied failure category without raw diagnostics."""
        title, message = _PRESENTATION_COPY.get(
            event.error_category,
            _PRESENTATION_COPY[BoothErrorCategory.UNEXPECTED],
        )
        self._title_label.setText(title)
        self._message_label.setText(message)


_PRESENTATION_COPY: dict[BoothErrorCategory, tuple[str, str]] = {
    BoothErrorCategory.CAMERA_UNAVAILABLE: (
        "Camera unavailable",
        "Please check the camera, then try again.",
    ),
    BoothErrorCategory.PHOTO_CAPTURE_FAILED: (
        "Couldn't take photo",
        "Please try again.",
    ),
    BoothErrorCategory.PHOTO_PROCESSING_FAILED: (
        "Couldn't prepare photo",
        "Please try again.",
    ),
    BoothErrorCategory.UNEXPECTED: (
        "Something went wrong",
        "Please return to start and try again.",
    ),
}
