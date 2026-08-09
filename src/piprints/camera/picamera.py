"""Picamera2 adapter for Raspberry Pi Camera Modules."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from piprints.camera.base import Camera, PreviewFrame
from piprints.camera.exceptions import (
    CameraCaptureError,
    CameraNotStartedError,
    CameraPreviewError,
    CameraStartupError,
)

logger = logging.getLogger(__name__)

_PREVIEW_SIZE = (1280, 720)


class _Picamera2(Protocol):
    """The subset of Picamera2 used by this adapter."""

    def start(self) -> None:
        """Start the camera."""

    def stop(self) -> None:
        """Stop the camera."""

    def capture_file(self, name: str) -> None:
        """Capture an image to a file."""

    def create_still_configuration(self, *, main: dict[str, object]) -> object:
        """Create a full-resolution still-image configuration."""

    def switch_mode_and_capture_file(
        self, configuration: object, file: str
    ) -> None:
        """Capture a file in another mode, then restore the current mode."""

    def set_controls(self, controls: dict[str, object]) -> None:
        """Set libcamera controls."""

    def create_preview_configuration(
        self, *, main: dict[str, object]
    ) -> object:
        """Create a camera preview configuration."""

    def configure(self, configuration: object) -> None:
        """Configure the camera stream."""

    def capture_array(self, name: str) -> _PreviewArray:
        """Return the next image frame from a configured stream."""


class _PreviewArray(Protocol):
    """The image-array behavior needed to create a PreviewFrame."""

    @property
    def shape(self) -> tuple[int, int, int]:
        """Return image height, width, and color channel count."""

    def tobytes(self) -> bytes:
        """Return packed image pixels."""


def _continuous_autofocus_mode() -> object:
    """Return libcamera's continuous autofocus mode for Camera Module 3."""
    from libcamera import controls

    return controls.AfModeEnum.Continuous


def _create_picamera2() -> _Picamera2:
    """Create a Picamera2 instance without leaking its dependency outward."""
    try:
        from picamera2 import Picamera2
    except ImportError as error:
        message = (
            "Picamera2 is unavailable. Run ./scripts/install.sh on Raspberry Pi OS."
        )
        raise CameraStartupError(message) from error

    return Picamera2()


class PiCamera(Camera):
    """Camera Module adapter backed by Picamera2.

    The optional ``camera`` parameter enables deterministic tests without
    importing or accessing Raspberry Pi camera hardware.
    """

    def __init__(self, camera: _Picamera2 | None = None) -> None:
        self._camera = camera
        self._started = False

    def start(self) -> None:
        """Start the camera and enable continuous autofocus once."""
        if self._started:
            return

        try:
            camera = self._get_camera()
            configuration = camera.create_preview_configuration(
                # libcamera's BGR888 name yields R, G, B bytes in memory, which
                # matches the standard RGB PreviewFrame contract.
                main={"size": _PREVIEW_SIZE, "format": "BGR888"}
            )
            camera.configure(configuration)
            camera.set_controls({"AfMode": _continuous_autofocus_mode()})
            camera.start()
        except Exception as error:
            logger.exception("Unable to start Raspberry Pi camera preview")
            raise CameraStartupError(
                "Unable to start Raspberry Pi camera preview."
            ) from error

        self._started = True
        logger.info("Raspberry Pi camera started with continuous autofocus")

    def capture(self, destination: Path) -> Path:
        """Capture an image to ``destination``.

        Parent directories are created if needed. The camera must be started
        before a capture can be requested.
        """
        if not self._started:
            raise CameraNotStartedError("Camera must be started before capture.")

        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            camera = self._get_camera()
            configuration = camera.create_still_configuration(
                main={"format": "BGR888"}
            )
            camera.switch_mode_and_capture_file(configuration, str(destination))
        except Exception as error:
            logger.exception("Unable to capture a Raspberry Pi camera still image")
            raise CameraCaptureError(
                "Unable to capture a camera still image."
            ) from error

        logger.info("Captured image to %s", destination)
        return destination

    def capture_preview_frame(self) -> PreviewFrame:
        """Return the next packed RGB frame from the live preview stream."""
        if not self._started:
            raise CameraNotStartedError("Camera must be started before preview.")

        try:
            image = self._get_camera().capture_array("main")
            height, width, channels = image.shape
            if channels != 3:
                raise CameraPreviewError(
                    f"Expected RGB preview frame with 3 channels; received {channels}."
                )
            return PreviewFrame(
                data=image.tobytes(),
                width=width,
                height=height,
                bytes_per_line=width * channels,
            )
        except CameraPreviewError:
            raise
        except Exception as error:
            logger.exception("Unable to capture a Raspberry Pi camera preview frame")
            raise CameraPreviewError(
                "Unable to capture a camera preview frame."
            ) from error

    def stop(self) -> None:
        """Stop the camera if it is running."""
        if not self._started:
            return

        self._get_camera().stop()
        self._started = False
        logger.info("Raspberry Pi camera stopped")

    def _get_camera(self) -> _Picamera2:
        """Return the configured hardware adapter, creating it when required."""
        if self._camera is None:
            self._camera = _create_picamera2()
        return self._camera
