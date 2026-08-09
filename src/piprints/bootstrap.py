"""Composition root for the PiPrints application."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from piprints.ui.screens.main_window import MainWindow


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application shared by all PiPrints UI components."""
    existing_application = QApplication.instance()
    if existing_application is not None:
        return existing_application

    application_arguments = list(arguments) if arguments is not None else sys.argv
    return QApplication(application_arguments)


def create_main_window() -> MainWindow:
    """Create the initial application window.

    Future concrete services are composed here and supplied to UI-facing
    controllers, keeping hardware and workflow setup outside the UI package.
    """
    return MainWindow()
