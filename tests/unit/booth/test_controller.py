"""Deterministic unit tests for the basic booth workflow controller."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from piprints.booth import (
    BoothCaptureError,
    BoothController,
    BoothEvent,
    BoothEventType,
    BoothSession,
    BoothState,
    BoothStateError,
    Countdown,
)
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import Layout, SinglePhotoLayout
from piprints.storage import FilesystemPhotoStorage
from tests.fakes import FakeCamera


def make_controller(camera: FakeCamera, capture_directory: Path) -> BoothController:
    """Create the default single-photo workflow for controller tests."""
    return BoothController(
        camera=camera,
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=SinglePhotoLayout(),
        photo_storage=FilesystemPhotoStorage(capture_directory.parent / "photos"),
        countdown=Countdown(3, delay=lambda _: None),
    )


class RecordingListener:
    """Record application events without requiring a presentation framework."""

    def __init__(self) -> None:
        self.events: list[BoothEvent] = []

    def on_booth_event(self, event: BoothEvent) -> None:
        """Store the event in publication order."""
        self.events.append(event)


def test_controller_starts_idle(tmp_path: Path) -> None:
    """A newly created booth begins at the live-preview state."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None
    assert controller.session is None


def test_begin_session_creates_the_active_session_and_prepares_the_booth(
    tmp_path: Path,
) -> None:
    """Session creation is the only transition from idle into preparation."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    session = controller.begin_session()

    assert isinstance(session, BoothSession)
    assert controller.session is session
    assert session.target_photo_count == 1
    assert controller.state is BoothState.PREPARING


def test_cannot_begin_a_second_active_session(tmp_path: Path) -> None:
    """Repeated start requests cannot replace in-flight session artifacts."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    session = controller.begin_session()

    with pytest.raises(BoothStateError, match="requires IDLE"):
        controller.begin_session()

    assert controller.session is session


def test_successful_capture_transitions_to_review(tmp_path: Path) -> None:
    """Countdown and capture move the controller into review with an image."""
    camera = FakeCamera()
    controller = make_controller(camera, tmp_path / "captures")

    controller.start_countdown()
    assert controller.state is BoothState.COUNTDOWN
    controller.run_countdown()
    assert controller.state is BoothState.CAPTURING

    captured_image = controller.capture()

    assert controller.state is BoothState.REVIEW
    assert controller.last_capture == captured_image
    assert captured_image.image.size == (2, 3)
    assert camera.capture_paths[0].parent == tmp_path / "captures"
    assert camera.capture_paths[0].suffix == ".jpg"


def test_countdown_execution_moves_the_controller_to_capturing(tmp_path: Path) -> None:
    """Countdown completion authorizes capture without performing it itself."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    listener = RecordingListener()
    controller.add_event_listener(listener)

    controller.start_countdown()
    controller.run_countdown()

    assert [
        event.countdown_value
        for event in listener.events
        if event.event_type is BoothEventType.COUNTDOWN_TICK
    ] == [3, 2, 1]
    assert controller.state is BoothState.CAPTURING


def test_controller_publishes_lifecycle_events_in_workflow_order(
    tmp_path: Path,
) -> None:
    """Listeners observe workflow changes without importing any UI framework."""
    listener = RecordingListener()
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    controller.add_event_listener(listener)

    controller.start_countdown()
    controller.run_countdown()
    controller.capture()

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
    ]
    state_events = [
        event
        for event in listener.events
        if event.event_type is BoothEventType.STATE_CHANGED
    ]
    assert [(event.previous_state, event.state) for event in state_events] == [
        (BoothState.IDLE, BoothState.PREPARING),
        (BoothState.PREPARING, BoothState.COUNTDOWN),
        (BoothState.COUNTDOWN, BoothState.CAPTURING),
        (BoothState.CAPTURING, BoothState.PROCESSING),
        (BoothState.PROCESSING, BoothState.REVIEW),
    ]


def test_listener_failure_does_not_interrupt_the_booth_workflow(tmp_path: Path) -> None:
    """A faulty observer is isolated from the controller's state transitions."""
    class FailingListener:
        def on_booth_event(self, event: BoothEvent) -> None:
            raise RuntimeError("listener unavailable")

    recording_listener = RecordingListener()
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    controller.add_event_listener(FailingListener())
    controller.add_event_listener(recording_listener)

    controller.begin_session()

    assert controller.state is BoothState.PREPARING
    assert [event.event_type for event in recording_listener.events] == [
        BoothEventType.SESSION_STARTED,
        BoothEventType.STATE_CHANGED,
    ]


def test_listener_is_not_registered_twice(tmp_path: Path) -> None:
    """Repeated registration cannot create duplicate notifications."""
    listener = RecordingListener()
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    controller.add_event_listener(listener)
    controller.add_event_listener(listener)
    controller.begin_session()

    assert len(listener.events) == 2


def test_completed_session_can_be_finished_and_return_to_idle(tmp_path: Path) -> None:
    """A reviewed result remains available until the lifecycle is finished."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    controller.start_countdown()
    controller.run_countdown()
    controller.capture()

    controller.complete_session()

    assert controller.state is BoothState.COMPLETE
    assert controller.session is not None
    assert controller.last_capture is not None

    controller.finish_session()

    assert controller.state is BoothState.IDLE
    assert controller.session is None
    assert controller.last_capture is None


def test_completing_a_session_persists_its_final_photo(tmp_path: Path) -> None:
    """Workflow completion delegates the final image to the storage boundary."""
    photo_directory = tmp_path / "photos"
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    controller.start_countdown()
    controller.run_countdown()
    final_photo = controller.capture()

    controller.complete_session()

    saved_paths = list(photo_directory.glob("*/*.png"))
    assert len(saved_paths) == 1
    assert final_photo is not None
    with Image.open(saved_paths[0]) as saved_image:
        assert saved_image.size == final_photo.image.size


def test_capture_before_countdown_raises_state_error(tmp_path: Path) -> None:
    """A still capture is not valid while the booth is displaying preview."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    with pytest.raises(BoothStateError):
        controller.capture()


def test_countdown_cannot_start_twice(tmp_path: Path) -> None:
    """The controller rejects a second countdown while one is already active."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    controller.start_countdown()

    with pytest.raises(BoothStateError):
        controller.start_countdown()


def test_retake_returns_to_idle_preview(tmp_path: Path) -> None:
    """Retake clears the reviewed image and makes another capture possible."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")
    controller.start_countdown()
    controller.run_countdown()
    controller.capture()

    controller.retake()

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None
    assert controller.session is None


def test_retake_outside_review_raises_state_error(tmp_path: Path) -> None:
    """Retake is only valid when a captured image is under review."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    with pytest.raises(BoothStateError):
        controller.retake()


def test_capture_failure_enters_error_and_preserves_cause(tmp_path: Path) -> None:
    """A camera failure is translated and leaves an explicit recovery boundary."""
    camera_error = RuntimeError("camera disconnected")
    controller = make_controller(
        FakeCamera(capture_error=camera_error), tmp_path / "captures"
    )
    controller.start_countdown()
    controller.run_countdown()

    with pytest.raises(BoothCaptureError) as error_info:
        controller.capture()

    assert error_info.value.__cause__ is camera_error
    assert controller.state is BoothState.ERROR
    assert controller.last_capture is None
    assert controller.session is None

    controller.reset_session()

    assert controller.state is BoothState.IDLE


def test_reset_session_requires_a_failed_workflow(tmp_path: Path) -> None:
    """Reset cannot discard a healthy or reviewed session accidentally."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    with pytest.raises(BoothStateError, match="requires ERROR"):
        controller.reset_session()


def test_capture_workflow_can_be_repeated(tmp_path: Path) -> None:
    """The same controller supports repeated capture and retake cycles."""
    camera = FakeCamera()
    controller = make_controller(camera, tmp_path / "captures")

    for _ in range(2):
        controller.start_countdown()
        controller.run_countdown()
        controller.capture()
        controller.retake()

    assert controller.state is BoothState.IDLE
    assert len(camera.capture_paths) == 2


class RecordingOperation:
    """Record the photo passed through a controller-owned pipeline."""

    def __init__(self) -> None:
        self.photos: list[Photo] = []

    def apply(self, photo: Photo) -> Photo:
        """Record and return the input photo unchanged."""
        self.photos.append(photo)
        return photo


class RecordingLayout:
    """Record processed photos received by the selected layout strategy."""

    required_photos = 1

    def __init__(self) -> None:
        self.photos: tuple[Photo, ...] | None = None

    def compose(self, photos: tuple[Photo, ...]) -> Photo:
        """Record and return the sole processed photo."""
        self.photos = photos
        return photos[0]


def test_capture_processes_photo_and_uses_selected_layout(tmp_path: Path) -> None:
    """The controller coordinates injected imaging collaborators after capture."""
    camera = FakeCamera()
    operation = RecordingOperation()
    layout: Layout = RecordingLayout()
    controller = BoothController(
        camera=camera,
        capture_directory=tmp_path / "captures",
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline([operation]),
        layout=layout,
        photo_storage=FilesystemPhotoStorage(tmp_path / "photos"),
    )

    controller.start_countdown()
    controller.run_countdown()
    final_photo = controller.capture()

    assert len(operation.photos) == 1
    assert layout.photos == (operation.photos[0],)
    assert final_photo is operation.photos[0]


class TwoPhotoRecordingLayout:
    """A layout double that proves controller composition waits for completion."""

    required_photos = 2

    def __init__(self) -> None:
        self.photos: tuple[Photo, ...] | None = None

    def compose(self, photos: tuple[Photo, ...]) -> Photo:
        """Record the complete session and return its first photo for testing."""
        self.photos = photos
        return photos[0]


def test_controller_collects_a_multi_photo_session_before_review(
    tmp_path: Path,
) -> None:
    """Incomplete sessions resume preview; only a complete session is reviewed."""
    layout = TwoPhotoRecordingLayout()
    controller = BoothController(
        camera=FakeCamera(),
        capture_directory=tmp_path / "captures",
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=layout,
        photo_storage=FilesystemPhotoStorage(tmp_path / "photos"),
    )

    controller.start_countdown()
    controller.run_countdown()
    assert controller.capture() is None
    assert controller.state is BoothState.PREPARING
    assert controller.session is not None
    assert controller.session.photo_count == 1
    assert controller.session.remaining_photos == 1
    assert layout.photos is None

    controller.start_countdown()
    controller.run_countdown()
    final_photo = controller.capture()

    assert controller.state is BoothState.REVIEW
    assert final_photo is controller.last_capture
    assert layout.photos is not None
    assert len(layout.photos) == 2
