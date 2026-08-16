"""Integration tests for kiosk-friendly booth failure presentation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from piprints.booth import (
    BoothCaptureError,
    BoothController,
    BoothErrorCategory,
    BoothEvent,
    BoothEventType,
    BoothState,
    Countdown,
)
from piprints.camera import CameraCaptureError
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import SinglePhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.ui import QtEventBridge
from piprints.ui.screens.error import ErrorScreen
from piprints.ui.screens.main_window import MainWindow
from tests.fakes import FakeCamera


@pytest.mark.parametrize(
    ("category", "title", "message"),
    [
        (
            BoothErrorCategory.CAMERA_UNAVAILABLE,
            "Camera unavailable",
            "Please check the camera, then try again.",
        ),
        (
            BoothErrorCategory.PHOTO_CAPTURE_FAILED,
            "Couldn't take photo",
            "Please try again.",
        ),
        (
            BoothErrorCategory.PHOTO_PROCESSING_FAILED,
            "Couldn't prepare photo",
            "Please try again.",
        ),
    ],
)
def test_error_screen_maps_categories_without_raw_diagnostics(
    category: BoothErrorCategory,
    title: str,
    message: str,
) -> None:
    """Customer copy is category-specific and never exposes exception detail."""
    application = QApplication.instance() or QApplication(["piprints"])
    recoveries: list[str] = []
    screen = ErrorScreen(lambda: recoveries.append("reset"))
    screen.resize(800, 480)
    screen.show()

    screen.show_error(
        BoothEvent(
            event_type=BoothEventType.ERROR,
            state=BoothState.ERROR,
            error_category=category,
            message="serial:///dev/ttyUSB0 traceback details",
        )
    )

    assert screen._title_label.text() == title
    assert screen._message_label.text() == message
    assert "ttyUSB" not in screen._title_label.text()
    assert "traceback" not in screen._message_label.text()
    assert screen._retry_button.minimumSize().toTuple() == (280, 88)
    assert screen._return_button.minimumSize().toTuple() == (280, 88)

    screen._retry_button.click()
    screen._return_button.click()
    assert recoveries == ["reset", "reset"]
    screen.close()
    application.processEvents()


def test_error_recovery_resets_the_controller_and_returns_home(tmp_path: Path) -> None:
    """The visible recovery action performs the valid ERROR-to-IDLE transition."""
    application = QApplication.instance() or QApplication(["piprints"])
    bridge = QtEventBridge()
    controller = BoothController(
        camera=FakeCamera(capture_error=CameraCaptureError("camera disconnected")),
        capture_directory=tmp_path / "captures",
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=SinglePhotoLayout(),
        photo_storage=FilesystemPhotoStorage(tmp_path / "photos"),
        countdown=Countdown(1, delay=lambda _: None),
        listeners=[bridge],
    )
    window = MainWindow(FakeCamera(), controller, bridge)

    controller.start_countdown()
    controller.run_countdown()
    with pytest.raises(BoothCaptureError, match="Unable to capture a photo"):
        controller.capture()

    assert controller.state is BoothState.ERROR
    assert window._pages.currentWidget() is window._error_screen
    assert window._error_screen._title_label.text() == "Couldn't take photo"

    window._error_screen._retry_button.click()

    assert controller.state is BoothState.IDLE
    assert window._pages.currentWidget() is window._home_screen
    window.close()
    application.processEvents()
