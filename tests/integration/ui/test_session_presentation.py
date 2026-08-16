"""Integration tests for multi-photo session presentation at the Qt boundary."""

from __future__ import annotations

import os
from inspect import getsource
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtWidgets import QApplication

from piprints.booth import (
    BoothController,
    BoothEvent,
    BoothEventType,
    BoothState,
    Countdown,
)
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import FourPhotoLayout
from piprints.storage import FilesystemPhotoStorage
from piprints.ui import QtEventBridge
from piprints.ui.photo_presentation import photo_to_pixmap
from piprints.ui.screens.booth import BoothScreen
from piprints.ui.widgets.countdown_presentation import CountdownPresentation
from tests.fakes import FakeCamera


def make_controller(capture_directory: Path) -> BoothController:
    """Create a hardware-independent controller using the standard grid layout."""
    return BoothController(
        camera=FakeCamera(),
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=FourPhotoLayout(),
        photo_storage=FilesystemPhotoStorage(capture_directory.parent / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
    )


def test_screen_progress_reads_the_controller_capture_session(tmp_path: Path) -> None:
    """Starting a session displays its first capture position without UI state."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    event_bridge = QtEventBridge()
    controller.add_event_listener(event_bridge)
    screen = BoothScreen(FakeCamera(), controller, event_bridge)

    screen._take_photo_button.click()

    assert screen._progress_label.text() == "Photo 1 of 4"

    screen.stop()
    screen.close()
    application.processEvents()


def test_layout_photo_converts_to_a_displayable_qt_pixmap() -> None:
    """The UI previews the composed Photo rather than recalculating its layout."""
    application = QApplication.instance() or QApplication(["piprints"])
    layout = FourPhotoLayout(canvas_width=44, canvas_height=44, margin=2, gutter=2)
    photos = [Photo(Image.new("RGB", (38, 38), color)) for color in ("red",) * 4]

    pixmap = photo_to_pixmap(layout.compose(photos))

    assert not pixmap.isNull()
    assert pixmap.size().toTuple() == (44, 44)
    application.processEvents()


def test_countdown_events_present_ticks_in_order_and_clear_on_capture(
    tmp_path: Path,
) -> None:
    """The preview overlay reflects ordered workflow events, not local timing."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    event_bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, event_bridge)
    screen.resize(800, 480)
    screen.show()
    application.processEvents()

    event_bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.STATE_CHANGED,
            previous_state=BoothState.PREPARING,
            state=BoothState.COUNTDOWN,
        )
    )
    observed: list[int | None] = []
    for value in (3, 2, 1):
        event_bridge.on_booth_event(
            BoothEvent(
                event_type=BoothEventType.COUNTDOWN_TICK,
                state=BoothState.COUNTDOWN,
                countdown_value=value,
            )
        )
        observed.append(screen._countdown_presentation.value)

    assert observed == [3, 2, 1]
    assert screen._countdown_presentation.isVisible()
    assert (
        screen._countdown_presentation.geometry()
        == screen._preview.parent().rect()
    )
    assert screen._countdown_presentation._number_label.font().pixelSize() == 240

    event_bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.STATE_CHANGED,
            previous_state=BoothState.COUNTDOWN,
            state=BoothState.CAPTURING,
        )
    )

    assert screen._countdown_presentation.value is None
    assert screen._countdown_presentation.isHidden()

    screen.close()
    application.processEvents()


def test_countdown_presentation_resets_without_owning_a_timing_timer(
    tmp_path: Path,
) -> None:
    """Session cleanup removes stale ticks; timing remains in the booth layer."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    event_bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, event_bridge)

    screen._countdown_presentation.show_tick(1)
    screen.reset_presentation()

    assert screen._countdown_presentation.value is None
    assert screen._countdown_presentation.isHidden()
    assert "QTimer" not in getsource(CountdownPresentation)
    assert "QTimer" not in getsource(BoothScreen)
    assert isinstance(controller._countdown, Countdown)
    application.processEvents()
