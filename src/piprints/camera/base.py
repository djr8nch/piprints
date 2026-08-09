"""Camera interfaces owned by PiPrints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreviewFrame:
    """An RGB image frame suitable for presentation by a UI."""

    data: bytes
    width: int
    height: int
    bytes_per_line: int


class Camera(ABC):
    """Minimal camera contract required by PiPrints workflows."""

    @abstractmethod
    def start(self) -> None:
        """Start the camera hardware."""

    @abstractmethod
    def capture(self, destination: Path) -> Path:
        """Capture an image to ``destination`` and return its path."""

    @abstractmethod
    def capture_preview_frame(self) -> PreviewFrame:
        """Return the next live-preview frame.

        This operation may block while waiting for a camera frame and must not
        be called from a UI thread.
        """

    @abstractmethod
    def stop(self) -> None:
        """Stop the camera hardware."""
