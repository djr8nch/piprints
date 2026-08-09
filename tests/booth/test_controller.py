"""Deterministic unit tests for the basic booth workflow controller."""

from __future__ import annotations

from pathlib import Path

import pytest

from piprints.booth import BoothCaptureError, BoothController, BoothState
from piprints.camera import Camera, PreviewFrame


class FakeCamera(Camera):
    """Camera fake that records still-capture requests without hardware."""

    def __init__(self, *, capture_error: Exception | None = None) -> None:
        self.capture_error = capture_error
        self.capture_paths: list[Path] = []

    def start(self) -> None:
        """Start the fake camera."""

    def capture(self, destination: Path) -> Path:
        """Record a still capture or raise the configured failure."""
        if self.capture_error is not None:
            raise self.capture_error
        self.capture_paths.append(destination)
        return destination

    def capture_preview_frame(self) -> PreviewFrame:
        """Return a minimal frame; preview is outside these controller tests."""
        return PreviewFrame(b"\x00\x00\x00", 1, 1, 3)

    def stop(self) -> None:
        """Stop the fake camera."""


def test_controller_starts_idle(tmp_path: Path) -> None:
    """A newly created booth begins at the live-preview state."""
    controller = BoothController(FakeCamera(), tmp_path / "captures")

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None


def test_successful_capture_transitions_to_review(tmp_path: Path) -> None:
    """Countdown and capture move the controller into review with an image."""
    camera = FakeCamera()
    controller = BoothController(camera, tmp_path / "captures")

    controller.start_countdown()
    assert controller.state is BoothState.COUNTDOWN

    captured_image = controller.capture()

    assert controller.state is BoothState.REVIEW
    assert controller.last_capture == captured_image
    assert captured_image.parent == tmp_path / "captures"
    assert captured_image.suffix == ".jpg"
    assert camera.capture_paths == [captured_image]


def test_retake_returns_to_idle_preview(tmp_path: Path) -> None:
    """Retake clears the reviewed image and makes another capture possible."""
    camera = FakeCamera()
    controller = BoothController(camera, tmp_path / "captures")
    controller.start_countdown()
    controller.capture()

    controller.retake()

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None


def test_capture_failure_returns_to_idle(tmp_path: Path) -> None:
    """A camera failure is translated and does not leave the booth stuck."""
    camera = FakeCamera(capture_error=RuntimeError("camera disconnected"))
    controller = BoothController(camera, tmp_path / "captures")
    controller.start_countdown()

    with pytest.raises(BoothCaptureError):
        controller.capture()

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None


def test_capture_workflow_can_be_repeated(tmp_path: Path) -> None:
    """The same controller supports repeated capture and retake cycles."""
    camera = FakeCamera()
    controller = BoothController(camera, tmp_path / "captures")

    for _ in range(2):
        controller.start_countdown()
        controller.capture()
        controller.retake()

    assert controller.state is BoothState.IDLE
    assert len(camera.capture_paths) == 2
