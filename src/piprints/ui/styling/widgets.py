"""Small helpers that assign semantic shared styling roles to Qt widgets."""

from __future__ import annotations

from enum import StrEnum

from PySide6.QtWidgets import QLabel, QPushButton


class ButtonRole(StrEnum):
    """Semantic roles supported by the default button stylesheet."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    ACCENT = "accent"
    QUIET = "quiet"
    ERROR = "error"


class StatusRole(StrEnum):
    """Semantic feedback roles supported by the shared status stylesheet."""

    NEUTRAL = "neutral"
    SUCCESS = "success"
    ERROR = "error"


def apply_button_role(button: QPushButton, role: ButtonRole) -> None:
    """Assign a semantic style role without embedding QSS in a screen."""
    button.setProperty("styleRole", role.value)


def set_status(label: QLabel, text: str, role: StatusRole) -> None:
    """Set customer feedback and its semantic visual treatment together."""
    label.setText(text)
    label.setProperty("statusRole", role.value)
    label.style().unpolish(label)
    label.style().polish(label)
