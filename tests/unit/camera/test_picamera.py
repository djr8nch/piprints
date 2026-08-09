"""Hardware-independent unit tests for the Picamera2 adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from piprints.camera import (
    CameraCaptureError,
    CameraNotStartedError,
    CameraPreviewError,
    CameraStartupError,
    PiCamera,
)


class FakePicamera2:
    """Small deterministic substitute for the external Picamera2 dependency."""

    def __init__(self) -> None:
        self.configuration: object | None = None
        self.capture_error: Exception | None = None
        self.capture_paths: list[str] = []
        self.controls: list[dict[str, object]] = []
        self.preview_error: Exception | None = None
        self.preview_images: list[FakePreviewArray] = []
        self.start_calls = 0
        self.start_error: Exception | None = None
        self.stop_calls = 0

    def start(self) -> None:
        if self.start_error is not None:
            raise self.start_error
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1

    def create_still_configuration(self, *, main: dict[str, object]) -> object:
        return main

    def switch_mode_and_capture_file(self, configuration: object, file: str) -> None:
        if self.capture_error is not None:
            raise self.capture_error
        self.configuration = configuration
        self.capture_paths.append(file)

    def set_controls(self, controls: dict[str, object]) -> None:
        self.controls.append(controls)

    def create_preview_configuration(self, *, main: dict[str, object]) -> object:
        return main

    def configure(self, configuration: object) -> None:
        self.configuration = configuration

    def capture_array(self, name: str) -> FakePreviewArray:
        assert name == "main"
        if self.preview_error is not None:
            raise self.preview_error
        return self.preview_images.pop(0)


class FakePreviewArray:
    """In-memory image substitute for Picamera2 preview-array output."""

    def __init__(self, shape: tuple[int, int, int], data: bytes) -> None:
        self.shape = shape
        self._data = data

    def tobytes(self) -> bytes:
        return self._data


@pytest.fixture
def autofocus_mode(monkeypatch: pytest.MonkeyPatch) -> object:
    """Avoid importing libcamera while exercising adapter lifecycle behavior."""
    mode = object()
    monkeypatch.setattr(
        "piprints.camera.picamera._continuous_autofocus_mode", lambda: mode
    )
    return mode


def test_capture_before_start_raises_domain_error(tmp_path: Path) -> None:
    """A still capture cannot be requested until the camera is running."""
    camera = PiCamera(FakePicamera2())

    with pytest.raises(CameraNotStartedError):
        camera.capture(tmp_path / "image.jpg")


def test_preview_before_start_raises_domain_error() -> None:
    """A preview frame cannot be requested until the camera is running."""
    camera = PiCamera(FakePicamera2())

    with pytest.raises(CameraNotStartedError):
        camera.capture_preview_frame()


def test_start_is_idempotent_and_enables_continuous_autofocus(
    autofocus_mode: object,
) -> None:
    """Starting twice configures and starts the hardware only once."""
    fake_camera = FakePicamera2()
    camera = PiCamera(fake_camera)

    camera.start()
    camera.start()

    assert fake_camera.start_calls == 1
    assert fake_camera.controls == [{"AfMode": autofocus_mode}]
    assert fake_camera.configuration == {
        "size": (1280, 720),
        "format": "BGR888",
    }


def test_stop_then_start_restarts_the_camera_lifecycle(
    autofocus_mode: object,
) -> None:
    """Stopping releases the lifecycle guard so the camera can start again."""
    fake_camera = FakePicamera2()
    camera = PiCamera(fake_camera)

    camera.start()
    camera.stop()
    camera.start()

    assert fake_camera.start_calls == 2
    assert fake_camera.stop_calls == 1
    assert fake_camera.controls == [{"AfMode": autofocus_mode}] * 2


def test_startup_failure_is_translated_with_its_cause(
    autofocus_mode: object,
) -> None:
    """External startup errors do not leak through the PiPrints API."""
    startup_error = RuntimeError("camera unavailable")
    fake_camera = FakePicamera2()
    fake_camera.start_error = startup_error

    with pytest.raises(CameraStartupError) as error_info:
        PiCamera(fake_camera).start()

    assert error_info.value.__cause__ is startup_error


def test_capture_creates_parent_directories_and_returns_destination(
    autofocus_mode: object, tmp_path: Path
) -> None:
    """Still captures use the requested Path and prepare its parent directory."""
    fake_camera = FakePicamera2()
    camera = PiCamera(fake_camera)
    destination = tmp_path / "captures" / "session" / "image.jpg"

    camera.start()
    result = camera.capture(destination)

    assert destination.parent.is_dir()
    assert result == destination
    assert fake_camera.capture_paths == [str(destination)]
    assert fake_camera.configuration == {"format": "BGR888"}


def test_capture_failure_is_translated_with_its_cause(
    autofocus_mode: object, tmp_path: Path
) -> None:
    """External still-capture failures are translated at the adapter boundary."""
    capture_error = RuntimeError("capture failed")
    fake_camera = FakePicamera2()
    fake_camera.capture_error = capture_error
    camera = PiCamera(fake_camera)

    camera.start()

    with pytest.raises(CameraCaptureError) as error_info:
        camera.capture(tmp_path / "image.jpg")

    assert error_info.value.__cause__ is capture_error


def test_capture_preview_frame_returns_a_piprints_owned_rgb_frame(
    autofocus_mode: object,
) -> None:
    """Preview output contains packed RGB data rather than a hardware frame."""
    fake_camera = FakePicamera2()
    fake_camera.preview_images.append(FakePreviewArray((2, 3, 3), b"a" * 18))
    camera = PiCamera(fake_camera)

    camera.start()
    frame = camera.capture_preview_frame()

    assert frame.data == b"a" * 18
    assert (frame.width, frame.height, frame.bytes_per_line) == (3, 2, 9)


def test_invalid_preview_channels_raise_domain_error(autofocus_mode: object) -> None:
    """Preview data with a non-RGB channel count is rejected explicitly."""
    fake_camera = FakePicamera2()
    fake_camera.preview_images.append(FakePreviewArray((2, 3, 4), b"a" * 24))
    camera = PiCamera(fake_camera)

    camera.start()

    with pytest.raises(CameraPreviewError, match="3 channels"):
        camera.capture_preview_frame()


def test_preview_capture_failure_is_translated_with_its_cause(
    autofocus_mode: object,
) -> None:
    """External preview failures are translated at the adapter boundary."""
    preview_error = RuntimeError("preview failed")
    fake_camera = FakePicamera2()
    fake_camera.preview_error = preview_error
    camera = PiCamera(fake_camera)

    camera.start()

    with pytest.raises(CameraPreviewError) as error_info:
        camera.capture_preview_frame()

    assert error_info.value.__cause__ is preview_error


def test_stop_is_idempotent(autofocus_mode: object) -> None:
    """Stopping twice stops the hardware only once."""
    fake_camera = FakePicamera2()
    camera = PiCamera(fake_camera)

    camera.start()
    camera.stop()
    camera.stop()

    assert fake_camera.stop_calls == 1
