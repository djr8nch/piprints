"""End-to-end application workflow tests without physical hardware or Qt."""

from __future__ import annotations

from pathlib import Path

import pytest

from piprints.booth import (
    BoothCaptureError,
    BoothController,
    BoothEvent,
    BoothEventType,
    BoothPrintError,
    BoothState,
    BoothStateError,
    BoothStorageError,
    Countdown,
)
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import SinglePhotoLayout
from piprints.imaging.operations import ResizeOperation
from piprints.printing import Printer, PrintResult
from piprints.storage import FilesystemPhotoStorage, PhotoStorage, StorageError
from tests.fakes import FakeCamera, FakePrinter


class RecordingListener:
    """Record emitted application events in workflow order."""

    def __init__(self) -> None:
        self.events: list[BoothEvent] = []

    def on_booth_event(self, event: BoothEvent) -> None:
        """Store one framework-independent booth event."""
        self.events.append(event)


class FailingStorage:
    """Deterministically fail persistence for output-status coverage."""

    def save(self, *_: object, **__: object) -> Path:
        """Raise the PiPrints storage boundary exception."""
        raise StorageError("storage unavailable")


def make_controller(
    camera: FakeCamera,
    capture_directory: Path,
    listener: RecordingListener,
    printer: Printer | None = None,
    photo_storage: PhotoStorage | None = None,
) -> BoothController:
    """Compose the real application collaborators around a fake camera."""
    return BoothController(
        camera=camera,
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline([ResizeOperation(4, 6)]),
        layout=SinglePhotoLayout(),
        photo_storage=photo_storage
        or FilesystemPhotoStorage(capture_directory.parent / "photos"),
        printer=printer,
        countdown=Countdown(3, delay=lambda _: None),
        listeners=[listener],
    )


def test_single_photo_session_runs_from_idle_through_completion_and_reset(
    tmp_path: Path,
) -> None:
    """Real workflow collaborators complete a deterministic booth session."""
    listener = RecordingListener()
    controller = make_controller(FakeCamera(), tmp_path / "captures", listener)

    assert controller.state is BoothState.IDLE

    controller.start_countdown()
    session = controller.session
    assert session is not None
    assert controller.state is BoothState.COUNTDOWN

    controller.run_countdown()
    assert controller.state is BoothState.CAPTURING

    final_photo = controller.capture()
    assert final_photo is not None
    assert controller.state is BoothState.REVIEW
    assert session.photo_count == 1
    assert session.captured_photos[0].image.size == (4, 6)
    assert session.final_photo is final_photo
    assert final_photo.image.size == (4, 6)

    controller.complete_session()
    assert controller.state is BoothState.COMPLETE
    output_saved_event = next(
        event
        for event in listener.events
        if event.event_type is BoothEventType.OUTPUT_SAVED
    )
    assert output_saved_event.output_path is not None
    assert output_saved_event.output_path.exists()
    controller.finish_session()

    assert controller.state is BoothState.IDLE
    assert controller.session is None
    assert controller.last_capture is None
    assert [event.event_type for event in listener.events] == [
        BoothEventType.SESSION_STARTED,
        BoothEventType.STATE_CHANGED,
        BoothEventType.STATE_CHANGED,
        BoothEventType.COUNTDOWN_TICK,
        BoothEventType.COUNTDOWN_TICK,
        BoothEventType.COUNTDOWN_TICK,
        BoothEventType.STATE_CHANGED,
        BoothEventType.PHOTO_CAPTURED,
        BoothEventType.STATE_CHANGED,
        BoothEventType.STATE_CHANGED,
        BoothEventType.REVIEW_READY,
        BoothEventType.OUTPUT_SAVED,
        BoothEventType.STATE_CHANGED,
        BoothEventType.SESSION_COMPLETED,
        BoothEventType.STATE_CHANGED,
    ]


def test_explicit_print_saves_then_prints_the_final_photo(tmp_path: Path) -> None:
    """A configured printer receives the final layout after digital saving."""
    listener = RecordingListener()
    printer = FakePrinter()
    controller = make_controller(
        FakeCamera(), tmp_path / "captures", listener, printer=printer
    )

    controller.start_countdown()
    controller.run_countdown()
    final_photo = controller.capture()
    controller.print_reviewed_output()

    assert final_photo is not None
    assert controller.state is BoothState.REVIEW
    assert printer.print_requests == (final_photo,)
    output_saved_event = next(
        event
        for event in listener.events
        if event.event_type is BoothEventType.OUTPUT_SAVED
    )
    print_completed_event = next(
        event
        for event in listener.events
        if event.event_type is BoothEventType.PRINT_COMPLETED
    )
    assert output_saved_event.output_path is not None
    assert output_saved_event.output_path.exists()
    assert print_completed_event.print_result == PrintResult(job_id="fake-print-1")
    with pytest.raises(BoothStateError, match="already been printed"):
        controller.print_reviewed_output()


def test_printer_failure_preserves_saved_output_and_review_state(
    tmp_path: Path,
) -> None:
    """A failed print remains recoverable without recapturing the final image."""
    listener = RecordingListener()
    printer = FakePrinter(fail=True)
    controller = make_controller(
        FakeCamera(), tmp_path / "captures", listener, printer=printer
    )

    controller.start_countdown()
    controller.run_countdown()
    final_photo = controller.capture()

    with pytest.raises(BoothPrintError) as error_info:
        controller.print_reviewed_output()

    output_saved_event = next(
        event
        for event in listener.events
        if event.event_type is BoothEventType.OUTPUT_SAVED
    )
    print_failed_event = next(
        event
        for event in listener.events
        if event.event_type is BoothEventType.PRINT_FAILED
    )
    assert error_info.value.__cause__ is not None
    assert controller.state is BoothState.REVIEW
    assert controller.last_capture is final_photo
    assert output_saved_event.output_path is not None
    assert output_saved_event.output_path.exists()
    assert print_failed_event.message == "Fake printer is configured to fail."
    assert printer.print_requests == ()

    printer.fail = False
    controller.print_reviewed_output()

    assert controller.state is BoothState.REVIEW
    assert printer.print_requests == (final_photo,)
    assert len(list((tmp_path / "photos").glob("*/*.png"))) == 1


def test_save_failure_emits_a_recoverable_output_event(tmp_path: Path) -> None:
    """A save failure reports status while retaining the reviewed final layout."""
    listener = RecordingListener()
    controller = make_controller(
        FakeCamera(),
        tmp_path / "captures",
        listener,
        photo_storage=FailingStorage(),
    )

    controller.start_countdown()
    controller.run_countdown()
    final_photo = controller.capture()

    with pytest.raises(BoothStorageError, match="Unable to save the completed photo"):
        controller.complete_session()

    save_failure = next(
        event
        for event in listener.events
        if event.event_type is BoothEventType.OUTPUT_SAVE_FAILED
    )
    assert controller.state is BoothState.REVIEW
    assert controller.last_capture is final_photo
    assert save_failure.message == "storage unavailable"


def test_camera_failure_enters_error_then_resets_cleanly(tmp_path: Path) -> None:
    """A capture failure preserves its cause and has a defined recovery path."""
    listener = RecordingListener()
    camera_error = RuntimeError("camera disconnected")
    controller = make_controller(
        FakeCamera(capture_error=camera_error), tmp_path / "captures", listener
    )

    controller.start_countdown()
    controller.run_countdown()

    with pytest.raises(BoothCaptureError) as error_info:
        controller.capture()

    assert error_info.value.__cause__ is camera_error
    assert controller.state is BoothState.ERROR
    assert controller.session is None
    assert [event.event_type for event in listener.events[-3:]] == [
        BoothEventType.STATE_CHANGED,
        BoothEventType.STATE_CHANGED,
        BoothEventType.ERROR,
    ]
    assert listener.events[-1].state is BoothState.ERROR
    assert listener.events[-1].message == "camera disconnected"

    controller.reset_session()

    assert controller.state is BoothState.IDLE
    assert listener.events[-1].event_type is BoothEventType.STATE_CHANGED
    assert listener.events[-1].previous_state is BoothState.ERROR
    assert listener.events[-1].state is BoothState.IDLE
