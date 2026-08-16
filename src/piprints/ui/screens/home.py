"""Touch-first idle presentation for the PiPrints booth."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from piprints.ui.styling import logo_path
from piprints.ui.styling.metrics import METRICS
from piprints.ui.styling.widgets import ButtonRole, apply_button_role


class HomeScreen(QWidget):
    """Present the single session-start action while the booth is idle.

    The screen receives an application-level callable rather than a controller
    or hardware dependency. This keeps it limited to presenting intent.
    """

    def __init__(self, show_layout_selection: Callable[[], None]) -> None:
        super().__init__()
        self._show_layout_selection = show_layout_selection

        self._logo_label = QLabel()
        self._logo_label.setAccessibleName("PiPrints logo")
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = QPixmap(str(logo_path()))
        if not logo.isNull():
            self._logo_label.setPixmap(
                logo.scaled(
                    190,
                    190,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        self._title_label = QLabel("PiPrints")
        self._title_label.setObjectName("homeTitle")
        self._title_label.setAccessibleName("PiPrints home")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setProperty("styleRole", "heroTitle")

        self._instruction_label = QLabel("Tap Start to choose your layout and theme")
        self._instruction_label.setAccessibleName("Start instructions")
        self._instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._instruction_label.setWordWrap(True)
        self._instruction_label.setProperty("styleRole", "secondaryText")

        self._start_button = QPushButton("Start")
        self._start_button.setObjectName("startButton")
        self._start_button.setAccessibleName("Start a photo booth session")
        self._start_button.setAccessibleDescription(
            "Opens layout and theme selection before live preview."
        )
        self._start_button.setMinimumSize(360, 104)
        self._start_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        apply_button_role(self._start_button, ButtonRole.PRIMARY)
        self._start_button.clicked.connect(self._request_session_start)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 20, 48, 20)
        layout.setSpacing(METRICS.spacing_medium)
        layout.addStretch(1)
        layout.addWidget(self._logo_label)
        layout.addWidget(self._title_label)
        layout.addWidget(self._instruction_label)
        layout.addSpacing(METRICS.spacing_small)
        layout.addWidget(self._start_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

    def reset_presentation(self) -> None:
        """Restore the idle action after a workflow returns to the home screen."""
        self._start_button.setEnabled(True)
        self._start_button.clearFocus()

    def _request_session_start(self) -> None:
        """Open layout selection through the presentation flow."""
        self._start_button.setEnabled(False)
        self._show_layout_selection()
