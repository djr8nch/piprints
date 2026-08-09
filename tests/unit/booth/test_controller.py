"""Deterministic unit tests for the basic booth workflow controller."""

from __future__ import annotations

from pathlib import Path

import pytest

from piprints.booth import (
    BoothCaptureError,
    BoothController,
    BoothState,
    BoothStateError,
)
from piprints.imaging import Photo, PhotoLoader, PhotoPipeline
from piprints.imaging.layouts import Layout, SinglePhotoLayout
from tests.fakes import FakeCamera


def make_controller(camera: FakeCamera, capture_directory: Path) -> BoothController:
    """Create the default single-photo workflow for controller tests."""
    return BoothController(
        camera=camera,
        capture_directory=capture_directory,
        photo_loader=PhotoLoader(),
        photo_pipeline=PhotoPipeline(),
        layout=SinglePhotoLayout(),
    )


def test_controller_starts_idle(tmp_path: Path) -> None:
    """A newly created booth begins at the live-preview state."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None


def test_successful_capture_transitions_to_review(tmp_path: Path) -> None:
    """Countdown and capture move the controller into review with an image."""
    camera = FakeCamera()
    controller = make_controller(camera, tmp_path / "captures")

    controller.start_countdown()
    assert controller.state is BoothState.COUNTDOWN

    captured_image = controller.capture()

    assert controller.state is BoothState.REVIEW
    assert controller.last_capture == captured_image
    assert captured_image.image.size == (2, 3)
    assert camera.capture_paths[0].parent == tmp_path / "captures"
    assert camera.capture_paths[0].suffix == ".jpg"


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
    controller.capture()

    controller.retake()

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None


def test_retake_outside_review_raises_state_error(tmp_path: Path) -> None:
    """Retake is only valid when a captured image is under review."""
    controller = make_controller(FakeCamera(), tmp_path / "captures")

    with pytest.raises(BoothStateError):
        controller.retake()


def test_capture_failure_returns_to_idle_and_preserves_cause(tmp_path: Path) -> None:
    """A camera failure is translated without leaving the booth stuck."""
    camera_error = RuntimeError("camera disconnected")
    controller = make_controller(
        FakeCamera(capture_error=camera_error), tmp_path / "captures"
    )
    controller.start_countdown()

    with pytest.raises(BoothCaptureError) as error_info:
        controller.capture()

    assert error_info.value.__cause__ is camera_error
    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None


def test_capture_workflow_can_be_repeated(tmp_path: Path) -> None:
    """The same controller supports repeated capture and retake cycles."""
    camera = FakeCamera()
    controller = make_controller(camera, tmp_path / "captures")

    for _ in range(2):
        controller.start_countdown()
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
    )

    controller.start_countdown()
    final_photo = controller.capture()

    assert len(operation.photos) == 1
    assert layout.photos == (operation.photos[0],)
    assert final_photo is operation.photos[0]
