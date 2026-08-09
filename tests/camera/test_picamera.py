"""Unit tests for the Raspberry Pi camera adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from piprints.camera import CameraNotStartedError, PiCamera


class FakePicamera2:
    """In-memory Picamera2 substitute for deterministic unit tests."""

    def __init__(self) -> None:
        self.configuration: object | None = None
        self.capture_paths: list[str] = []
        self.preview_images: list[FakePreviewArray] = []
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

    def create_preview_configuration(self, *, main: dict[str, object]) -> object:
        return main

    def configure(self, configuration: object) -> None:
        self.configuration = configuration

    def capture_array(self, name: str) -> FakePreviewArray:
        assert name == "main"
        return self.preview_images.pop(0)


class FakePreviewArray:
    """In-memory RGB image substitute for Picamera2 preview output."""

    def __init__(self, shape: tuple[int, int, int], data: bytes) -> None:
        self.shape = shape
        self._data = data

    def tobytes(self) -> bytes:
        return self._data


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
    assert fake_camera.configuration == {
        "size": (1280, 720),
        "format": "BGR888",
    }


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


def test_capture_preview_frame_returns_a_piprints_owned_rgb_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preview output contains packed RGB data rather than a hardware frame."""
    fake_camera = FakePicamera2()
    fake_camera.preview_images.append(FakePreviewArray((2, 3, 3), b"a" * 18))
    camera = PiCamera(fake_camera)
    monkeypatch.setattr(
        "piprints.camera.picamera._continuous_autofocus_mode", lambda: object()
    )

    camera.start()
    frame = camera.capture_preview_frame()

    assert frame.data == b"a" * 18
    assert (frame.width, frame.height, frame.bytes_per_line) == (3, 2, 9)


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
