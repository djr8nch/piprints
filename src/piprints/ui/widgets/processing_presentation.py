"""Minimal Qt feedback for application-owned photo preparation."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from piprints.ui.styling.metrics import METRICS


class ProcessingPresentation(QWidget):
    """Present indeterminate processing feedback without owning processing work."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("processingPresentation")
        self._message_label = QLabel("Preparing your photo…")
        self._message_label.setAccessibleName("Photo processing")
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_label.setProperty("styleRole", "screenTitle")

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
        layout.setSpacing(METRICS.spacing_large)
        layout.addStretch()
        layout.addWidget(self._message_label)
        layout.addWidget(self._indicator, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
