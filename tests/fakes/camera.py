"""A small hardware-independent fake for the PiPrints Camera contract."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from piprints.camera import Camera, PreviewFrame


class FakeCamera(Camera):
    """Record camera operations and optionally raise a configured capture error."""

    def __init__(
        self,
        *,
        capture_error: Exception | None = None,
        preview_frame: PreviewFrame | None = None,
    ) -> None:
        self.capture_error = capture_error
        self.capture_paths: list[Path] = []
        self.preview_frame = preview_frame or PreviewFrame(b"\x00\x00\x00", 1, 1, 3)
        self.start_calls = 0
        self.stop_calls = 0

    def start(self) -> None:
        """Record camera startup."""
        self.start_calls += 1

    def capture(self, destination: Path) -> Path:
        """Record a still capture or raise the configured failure."""
        if self.capture_error is not None:
            raise self.capture_error
        destination.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (2, 3), "black").save(destination)
        self.capture_paths.append(destination)
        return destination

    def capture_preview_frame(self) -> PreviewFrame:
        """Return the configured hardware-independent preview frame."""
        return self.preview_frame

    def stop(self) -> None:
        """Record camera shutdown."""
        self.stop_calls += 1
