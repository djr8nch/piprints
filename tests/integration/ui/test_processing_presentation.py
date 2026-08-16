"""Integration tests for processing-state feedback in the Qt presentation."""

from __future__ import annotations

import os
from inspect import getsource
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from piprints.booth import (
    BoothController,
    BoothEvent,
    BoothEventType,
    BoothState,
    Countdown,
)
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import FourPhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.ui import QtEventBridge
from piprints.ui.screens.booth import BoothScreen
from piprints.ui.screens.main_window import MainWindow
from piprints.ui.widgets.processing_presentation import ProcessingPresentation
from tests.fakes import FakeCamera


def make_controller(capture_directory: Path) -> BoothController:
    """Create a hardware-independent controller for presentation tests."""
    return BoothController(
        camera=FakeCamera(),
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        photo_storage=FilesystemPhotoStorage(capture_directory.parent / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
    )


def state_event(previous: BoothState, current: BoothState) -> BoothEvent:
    """Build a state transition event without running hardware work."""
    return BoothEvent(
        event_type=BoothEventType.STATE_CHANGED,
        previous_state=previous,
        state=current,
    )


def test_processing_state_shows_minimal_presentation_at_800_by_480(
    tmp_path: Path,
) -> None:
    """The processing page fits the production touchscreen without clutter."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, bridge)
    screen.resize(800, 480)
    screen.show()
    application.processEvents()

    bridge.on_booth_event(state_event(BoothState.CAPTURING, BoothState.PROCESSING))

    processing = screen._processing_presentation
    assert screen._pages.currentWidget() is processing
    assert processing._message_label.text() == "Preparing your photo…"
    assert processing._indicator.minimum() == processing._indicator.maximum() == 0
    assert processing.rect().contains(processing._indicator.geometry())
    assert processing._indicator.width() <= 460

    screen.close()
    application.processEvents()


def test_review_and_error_states_leave_processing_presentation(tmp_path: Path) -> None:
    """Terminal processing outcomes cannot leave stale wait feedback visible."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, bridge)

    bridge.on_booth_event(state_event(BoothState.CAPTURING, BoothState.PROCESSING))
    bridge.on_booth_event(state_event(BoothState.PROCESSING, BoothState.REVIEW))
    assert screen._pages.currentIndex() == 1

    bridge.on_booth_event(state_event(BoothState.CAPTURING, BoothState.PROCESSING))
    bridge.on_booth_event(state_event(BoothState.PROCESSING, BoothState.ERROR))
    assert screen._pages.currentIndex() == 0

    screen.reset_presentation()
    assert screen._pages.currentIndex() == 0
    application.processEvents()


def test_main_window_routes_processing_error_to_error_presentation(
    tmp_path: Path,
) -> None:
    """A workflow error replaces processing feedback with a recovery screen."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    bridge = QtEventBridge()
    window = MainWindow(FakeCamera(), controller, bridge)

    bridge.on_booth_event(state_event(BoothState.CAPTURING, BoothState.PROCESSING))
    assert window._pages.currentWidget() is window._booth_screen
    assert (
        window._booth_screen._pages.currentWidget()
        is window._booth_screen._processing_presentation
    )

    bridge.on_booth_event(state_event(BoothState.PROCESSING, BoothState.ERROR))
    assert window._pages.currentWidget() is window._error_screen

    window.close()
    application.processEvents()


def test_processing_widget_has_no_image_pipeline_dependency() -> None:
    """The UI observes state only; it does not perform image processing."""
    source = getsource(ProcessingPresentation)

    assert "PhotoPipeline" not in source
    assert ".process(" not in source
