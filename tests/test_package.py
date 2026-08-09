"""Basic package-level checks that do not require Raspberry Pi hardware."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from piprints import __version__
from piprints.bootstrap import create_application, create_main_window
from piprints.camera import Camera, PreviewFrame


class FakeCamera(Camera):
    """Camera contract implementation for the application-shell test."""

    def start(self) -> None:
        """Start the fake camera."""

    def capture(self, destination: Path) -> Path:
        """Capture is not needed by this test."""
        return destination

    def capture_preview_frame(self) -> PreviewFrame:
        """Return a small frame if the preview worker starts."""
        return PreviewFrame(b"\x00\x00\x00", 1, 1, 3)

    def stop(self) -> None:
        """Stop the fake camera."""


def test_package_exposes_a_version() -> None:
    """Expose version metadata for callers and packaging tools."""
    assert __version__ == "0.1.0"


def test_application_shell_can_be_created() -> None:
    """Create the shell without requiring a display or Raspberry Pi hardware."""
    application = create_application(["piprints"])
    window = create_main_window(FakeCamera())

    assert application is not None
    assert window.windowTitle() == "PiPrints Camera Preview"

    window.close()
