"""Integration tests for multi-photo session presentation at the Qt boundary."""

from __future__ import annotations

import os
from inspect import getsource
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from piprints.booth import (
    BoothController,
    BoothEvent,
    BoothEventType,
    BoothPrintError,
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


class LifecycleRecorder:
    """Record the controller lifecycle requested by the review presentation."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.session = None
        self.printer_available = False
        self.output_saved = False

    def complete_session(self) -> None:
        """Record persistent completion."""
        self.calls.append("complete")

    def finish_session(self) -> None:
        """Record return to the idle lifecycle boundary."""
        self.calls.append("finish")


class PrintLifecycleRecorder(LifecycleRecorder):
    """Record one printer request made by the review presentation."""

    def __init__(self) -> None:
        super().__init__()
        self.printer_available = True

    def print_reviewed_output(self) -> None:
        """Record application-owned printing without hardware dependencies."""
        self.calls.append("print")


class FailingPrintLifecycleRecorder(PrintLifecycleRecorder):
    """Fail a print request while keeping the displayed review result intact."""

    def print_reviewed_output(self) -> None:
        """Raise the same application exception used for printer failures."""
        self.calls.append("print")
        raise BoothPrintError("Printer unavailable.")


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


def test_review_displays_the_final_layout_with_preserved_aspect_ratio(
    tmp_path: Path,
) -> None:
    """The review screen receives the composed output, never a raw capture."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = make_controller(tmp_path / "captures")
    event_bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, event_bridge)
    screen.resize(800, 480)
    screen.show()
    application.processEvents()

    raw_capture = Photo(Image.new("RGB", (30, 30), "red"))
    final_layout = Photo(Image.new("RGB", (240, 120), "blue"))
    assert raw_capture != final_layout
    event_bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.REVIEW_READY,
            state=BoothState.REVIEW,
            photo=final_layout,
        )
    )
    application.processEvents()

    displayed = screen._review_label.pixmap()
    assert displayed is not None
    assert screen._review_pixmap is not None
    assert screen._review_pixmap.toImage().pixelColor(0, 0) == QColor("blue")
    assert displayed.width() * 120 == displayed.height() * 240
    assert screen._review_label.height() > screen.height() // 2
    assert screen._done_button.minimumWidth() >= 220
    assert screen._done_button.minimumHeight() >= 72
    assert not screen._print_button.isEnabled()
    assert screen._review_status_label.text() == "Printer unavailable"

    event_bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.STATE_CHANGED,
            previous_state=BoothState.IDLE,
            state=BoothState.PREPARING,
        )
    )
    assert screen._review_pixmap is None
    assert screen._review_label.pixmap().isNull()

    screen.reset_presentation()
    assert screen._review_pixmap is None
    assert screen._review_label.pixmap().isNull()
    screen.close()
    application.processEvents()


def test_done_requests_the_controller_completion_lifecycle() -> None:
    """The review widget delegates completion rather than resetting controller state."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = LifecycleRecorder()
    event_bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, event_bridge)  # type: ignore[arg-type]
    screen._show_review(Photo(Image.new("RGB", (2, 2), "blue")))

    screen._done_button.click()
    assert screen._completion_worker is not None
    assert screen._completion_worker.wait(1000)
    assert controller.calls == ["complete", "finish"]

    screen.close()
    application.processEvents()


def test_print_requests_the_application_api_only_once_per_touch_sequence() -> None:
    """Rapid taps disable the action before a second worker can be requested."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = PrintLifecycleRecorder()
    event_bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, event_bridge)  # type: ignore[arg-type]
    screen.resize(800, 480)
    screen.show()
    screen._show_review(Photo(Image.new("RGB", (2, 2), "blue")))

    screen._print_button.click()
    screen._print_button.click()

    assert not screen._print_button.isEnabled()
    assert screen._save_status_label.text() == "Saving…"
    assert screen._print_status_label.text() == "Printing…"
    assert screen._print_worker is not None
    assert screen._print_worker.wait(1000)
    assert controller.calls == ["print"]
    assert "PrimuzThermalPrinter" not in getsource(BoothScreen)
    assert "SerialTransport" not in getsource(BoothScreen)
    assert "UsbPrinterTransport" not in getsource(BoothScreen)
    assert "/dev/usb/lp0" not in getsource(BoothScreen)
    assert screen._print_button.minimumWidth() >= 136
    assert screen._print_button.minimumHeight() >= 72

    screen.close()
    application.processEvents()


def test_print_failure_keeps_review_photo_and_done_available() -> None:
    """A failed print is recoverable without removing the completed layout."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = FailingPrintLifecycleRecorder()
    event_bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, event_bridge)  # type: ignore[arg-type]
    final_layout = Photo(Image.new("RGB", (20, 10), "blue"))
    screen._show_review(final_layout)
    displayed_pixmap = screen._review_pixmap

    screen._print_button.click()
    assert screen._print_worker is not None
    assert screen._print_worker.wait(1000)
    application.processEvents()

    assert controller.calls == ["print"]
    assert screen._review_pixmap is displayed_pixmap
    assert screen._done_button.isEnabled()
    assert screen._print_button.isEnabled()
    assert screen._review_status_label.text() == "Print failed"

    screen.close()
    application.processEvents()


def test_review_footer_keeps_save_and_print_statuses_independent() -> None:
    """A print failure explicitly retains the confirmed digital save result."""
    application = QApplication.instance() or QApplication(["piprints"])
    controller = PrintLifecycleRecorder()
    event_bridge = QtEventBridge()
    screen = BoothScreen(FakeCamera(), controller, event_bridge)  # type: ignore[arg-type]
    screen.resize(800, 480)
    screen.show()
    screen._show_review(Photo(Image.new("RGB", (20, 10), "blue")))

    screen._print_status_label.setText("Printing…")
    event_bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.OUTPUT_SAVE_FAILED,
            state=BoothState.REVIEW,
            message="storage unavailable",
        )
    )
    assert screen._save_status_label.text() == "Save failed"
    assert screen._print_status_label.text() == ""

    event_bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.OUTPUT_SAVED,
            state=BoothState.REVIEW,
            output_path=Path("/runtime/photos/final.png"),
        )
    )
    event_bridge.on_booth_event(
        BoothEvent(
            event_type=BoothEventType.PRINT_FAILED,
            state=BoothState.REVIEW,
            message="printer offline",
        )
    )

    assert screen._save_status_label.text() == "✓ Saved"
    assert screen._print_status_label.text() == "Print failed"
    assert screen._done_button.isEnabled()
    assert screen._print_button.isEnabled()
    assert screen._review_label.height() > screen.height() // 2

    screen.reset_presentation()
    assert screen._save_status_label.text() == ""
    assert screen._print_status_label.text() == ""
    screen.close()
    application.processEvents()
