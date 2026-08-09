"""Contracts for transformations applied to individual photos."""

from __future__ import annotations

from typing import Protocol

from piprints.imaging.models import Photo


class PhotoOperation(Protocol):
    """Transform one photo into another photo."""

    def apply(self, photo: Photo) -> Photo:
        """Return the transformed photo."""
