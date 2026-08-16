"""End-to-end application workflow tests without physical hardware or Qt."""

from __future__ import annotations

from pathlib import Path

import pytest

from piprints.booth import (
    BoothCaptureError,
    BoothController,
    BoothEvent,
    BoothEventType,
    BoothState,
    Countdown,
)
from piprints.imaging import PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import SinglePhotoLayout
from piprints.imaging.operations import ResizeOperation
from tests.fakes import FakeCamera


class RecordingListener:
    """Record emitted application events in workflow order."""

    def __init__(self) -> None:
        self.events: list[BoothEvent] = []

    def on_booth_event(self, event: BoothEvent) -> None:
        """Store one framework-independent booth event."""
        self.events.append(event)


def make_controller(
    camera: FakeCamera,
    capture_directory: Path,
    listener: RecordingListener,
) -> BoothController:
    """Compose the real application collaborators around a fake camera."""
    return BoothController(
        camera=camera,
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline([ResizeOperation(4, 6)]),
        layout=SinglePhotoLayout(),
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
        BoothEventType.STATE_CHANGED,
        BoothEventType.SESSION_COMPLETED,
        BoothEventType.STATE_CHANGED,
    ]


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
