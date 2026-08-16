"""Simple recovery presentation for application-level booth failures."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from piprints.booth import BoothErrorCategory, BoothEvent


class ErrorScreen(QWidget):
    """Show a user-friendly error and provide a route back to idle."""

    def __init__(self, reset_session: Callable[[], None]) -> None:
        super().__init__()
        self._reset_session = reset_session
        self._title_label = QLabel("Something went wrong")
        self._title_label.setAccessibleName("Booth error")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPixelSize(36)
        title_font.setWeight(QFont.Weight.DemiBold)
        self._title_label.setFont(title_font)
        self._message_label = QLabel("Please return to start and try again.")
        self._message_label.setAccessibleName("Error recovery instructions")
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_label.setWordWrap(True)
        message_font = QFont()
        message_font.setPixelSize(22)
        self._message_label.setFont(message_font)

        self._return_button = QPushButton("Return to start")
        self._return_button.setObjectName("errorReturnButton")
        self._return_button.setAccessibleName("Return to start")
        self._return_button.setAccessibleDescription(
            "Clear this error and return to the PiPrints home screen."
        )
        self._return_button.setMinimumSize(320, 88)
        self._return_button.setStyleSheet(
            "QPushButton { font-size: 26px; font-weight: bold; padding: 12px 32px; }"
            "QPushButton:pressed { background-color: #555555; }"
            "QPushButton:focus { border: 3px solid #77baff; }"
        )
        self._return_button.clicked.connect(self._reset_session)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 48, 64, 48)
        layout.setSpacing(32)
        layout.addStretch()
        layout.addWidget(self._title_label)
        layout.addWidget(self._message_label)
        layout.addWidget(self._return_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #151515; color: white;")

    def show_error(self, event: BoothEvent) -> None:
        """Present application-supplied failure category without raw diagnostics."""
        title, message = _PRESENTATION_COPY.get(
            event.error_category,
            _PRESENTATION_COPY[BoothErrorCategory.UNEXPECTED],
        )
        self._title_label.setText(title)
        self._message_label.setText(message)

    def reset_presentation(self) -> None:
        """Discard the prior customer's error before the home screen is shown."""
        self._title_label.setText("Something went wrong")
        self._message_label.clear()


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
