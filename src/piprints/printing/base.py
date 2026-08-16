"""Contracts for submitting prepared PiPrints photos to printers."""

from __future__ import annotations

from typing import Protocol

from piprints.imaging import Photo
from piprints.printing.models import PrintResult


class Printer(Protocol):
    """Submit a fully prepared photo to a physical printer."""

    def print_photo(self, photo: Photo) -> PrintResult:
        """Request printing of ``photo`` and return its submission result."""
