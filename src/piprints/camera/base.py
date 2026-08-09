"""Camera interfaces owned by PiPrints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Camera(ABC):
    """Minimal camera contract required by PiPrints workflows."""

    @abstractmethod
    def start(self) -> None:
        """Start the camera hardware."""

    @abstractmethod
    def capture(self, destination: Path) -> Path:
        """Capture an image to ``destination`` and return its path."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the camera hardware."""
