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
from tests.fakes import FakeCamera


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


def test_capture_before_countdown_raises_state_error(tmp_path: Path) -> None:
    """A still capture is not valid while the booth is displaying preview."""
    controller = BoothController(FakeCamera(), tmp_path / "captures")

    with pytest.raises(BoothStateError):
        controller.capture()


def test_countdown_cannot_start_twice(tmp_path: Path) -> None:
    """The controller rejects a second countdown while one is already active."""
    controller = BoothController(FakeCamera(), tmp_path / "captures")
    controller.start_countdown()

    with pytest.raises(BoothStateError):
        controller.start_countdown()


def test_retake_returns_to_idle_preview(tmp_path: Path) -> None:
    """Retake clears the reviewed image and makes another capture possible."""
    controller = BoothController(FakeCamera(), tmp_path / "captures")
    controller.start_countdown()
    controller.capture()

    controller.retake()

    assert controller.state is BoothState.IDLE
    assert controller.last_capture is None


def test_retake_outside_review_raises_state_error(tmp_path: Path) -> None:
    """Retake is only valid when a captured image is under review."""
    controller = BoothController(FakeCamera(), tmp_path / "captures")

    with pytest.raises(BoothStateError):
        controller.retake()


def test_capture_failure_returns_to_idle_and_preserves_cause(tmp_path: Path) -> None:
    """A camera failure is translated without leaving the booth stuck."""
    camera_error = RuntimeError("camera disconnected")
    controller = BoothController(
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
    controller = BoothController(camera, tmp_path / "captures")

    for _ in range(2):
        controller.start_countdown()
        controller.capture()
        controller.retake()

    assert controller.state is BoothState.IDLE
    assert len(camera.capture_paths) == 2
