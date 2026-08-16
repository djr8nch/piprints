"""Minimal Qt feedback for application-owned photo preparation."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget


class ProcessingPresentation(QWidget):
    """Present indeterminate processing feedback without owning processing work."""

    def __init__(self) -> None:
        super().__init__()
        self._message_label = QLabel("Preparing your photo…")
        self._message_label.setAccessibleName("Photo processing")
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_font = QFont()
        message_font.setPixelSize(38)
        message_font.setWeight(QFont.Weight.DemiBold)
        self._message_label.setFont(message_font)

        self._indicator = QProgressBar()
        self._indicator.setAccessibleName("Photo processing in progress")
        self._indicator.setAccessibleDescription(
            "PiPrints is preparing the final photo."
        )
        self._indicator.setRange(0, 0)
        self._indicator.setTextVisible(False)
        self._indicator.setFixedHeight(18)
        self._indicator.setMaximumWidth(460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 48, 64, 48)
        layout.setSpacing(28)
        layout.addStretch()
        layout.addWidget(self._message_label)
        layout.addWidget(self._indicator, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #151515; color: white;")
