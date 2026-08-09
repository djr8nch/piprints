"""Picamera2 adapter for Raspberry Pi Camera Modules."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from piprints.camera.base import Camera
from piprints.camera.exceptions import CameraNotStartedError

logger = logging.getLogger(__name__)


class _Picamera2(Protocol):
    """The subset of Picamera2 used by this adapter."""

    def start(self) -> None:
        """Start the camera."""

    def stop(self) -> None:
        """Stop the camera."""

    def capture_file(self, name: str) -> None:
        """Capture an image to a file."""

    def set_controls(self, controls: dict[str, object]) -> None:
        """Set libcamera controls."""


def _continuous_autofocus_mode() -> object:
    """Return libcamera's continuous autofocus mode for Camera Module 3."""
    from libcamera import controls

    return controls.AfModeEnum.Continuous


class PiCamera(Camera):
    """Camera Module adapter backed by Picamera2.

    The optional ``camera`` parameter enables deterministic tests without
    importing or accessing Raspberry Pi camera hardware.
    """

    def __init__(self, camera: _Picamera2 | None = None) -> None:
        if camera is None:
            from picamera2 import Picamera2

            camera = Picamera2()

        self._camera = camera
        self._started = False

    def start(self) -> None:
        """Start the camera and enable continuous autofocus once."""
        if self._started:
            return

        self._camera.set_controls({"AfMode": _continuous_autofocus_mode()})
        self._camera.start()
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
        self._camera.capture_file(str(destination))
        logger.info("Captured image to %s", destination)
        return destination

    def stop(self) -> None:
        """Stop the camera if it is running."""
        if not self._started:
            return

        self._camera.stop()
        self._started = False
        logger.info("Raspberry Pi camera stopped")
