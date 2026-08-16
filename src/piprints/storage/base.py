"""Contracts for persisting completed PiPrints photos."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

from piprints.imaging import Photo


class PhotoStorage(Protocol):
    """Persist a completed photo and report its filesystem location."""

    def save(self, photo: Photo, *, session_id: UUID) -> Path:
        """Save ``photo`` for ``session_id`` and return its resulting path."""
