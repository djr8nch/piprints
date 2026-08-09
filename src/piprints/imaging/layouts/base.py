"""Contracts for composing processed photos into final images."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from piprints.imaging.models import Photo


class Layout(Protocol):
    """Compose a required number of processed photos into one final photo."""

    @property
    def required_photos(self) -> int:
        """Return the number of captures needed to compose this layout."""

    def compose(self, photos: Sequence[Photo]) -> Photo:
        """Return the final photo composed from processed input photos."""
