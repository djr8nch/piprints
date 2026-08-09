"""Composition root for the PiPrints application."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtWidgets import QApplication

from piprints.booth import BoothController
from piprints.camera import Camera, PiCamera
from piprints.ui.screens.main_window import MainWindow


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Create the Qt application shared by all PiPrints UI components."""
    existing_application = QApplication.instance()
    if existing_application is not None:
        return existing_application

    application_arguments = list(arguments) if arguments is not None else sys.argv
    return QApplication(application_arguments)


def create_camera() -> Camera:
    """Create the Raspberry Pi camera used by the application."""
    return PiCamera()


def create_booth(
    camera: Camera, capture_directory: Path | None = None
) -> BoothController:
    """Create the booth workflow with its runtime capture location."""
    directory = capture_directory or Path.cwd() / "captures"
    return BoothController(camera, directory)


def create_main_window(camera: Camera, booth: BoothController) -> MainWindow:
    """Create the main window with its camera dependency.

    Camera construction remains in this composition root so UI code depends on
    the PiPrints camera contract rather than hardware implementations.
    """
    return MainWindow(camera, booth)
