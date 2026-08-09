"""Unit tests for the Raspberry Pi camera adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from piprints.camera import CameraNotStartedError, PiCamera


class FakePicamera2:
    """In-memory Picamera2 substitute for deterministic unit tests."""

    def __init__(self) -> None:
        self.capture_paths: list[str] = []
        self.controls: list[dict[str, object]] = []
        self.start_calls = 0
        self.stop_calls = 0

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1

    def capture_file(self, name: str) -> None:
        self.capture_paths.append(name)

    def set_controls(self, controls: dict[str, object]) -> None:
        self.controls.append(controls)


def test_capture_before_start_raises_domain_error(tmp_path: Path) -> None:
    """A capture cannot be requested until the camera is running."""
    camera = PiCamera(FakePicamera2())

    with pytest.raises(CameraNotStartedError):
        camera.capture(tmp_path / "image.jpg")


def test_start_is_idempotent_and_enables_continuous_autofocus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Starting twice configures and starts the hardware only once."""
    fake_camera = FakePicamera2()
    camera = PiCamera(fake_camera)
    autofocus_mode = object()
    monkeypatch.setattr(
        "piprints.camera.picamera._continuous_autofocus_mode", lambda: autofocus_mode
    )

    camera.start()
    camera.start()

    assert fake_camera.start_calls == 1
    assert fake_camera.controls == [{"AfMode": autofocus_mode}]


def test_capture_creates_parent_directories_and_returns_destination(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Captures use the requested Path and prepare its parent directory."""
    fake_camera = FakePicamera2()
    camera = PiCamera(fake_camera)
    monkeypatch.setattr(
        "piprints.camera.picamera._continuous_autofocus_mode", lambda: object()
    )
    destination = tmp_path / "captures" / "session" / "image.jpg"

    camera.start()
    result = camera.capture(destination)

    assert destination.parent.is_dir()
    assert result == destination
    assert fake_camera.capture_paths == [str(destination)]


def test_stop_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stopping twice stops the hardware only once."""
    fake_camera = FakePicamera2()
    camera = PiCamera(fake_camera)
    monkeypatch.setattr(
        "piprints.camera.picamera._continuous_autofocus_mode", lambda: object()
    )

    camera.start()
    camera.stop()
    camera.stop()

    assert fake_camera.stop_calls == 1
