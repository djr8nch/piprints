"""Unit tests for the ResizeOperation."""

from __future__ import annotations

import pytest
from PIL import Image

from piprints.imaging import Photo
from piprints.imaging.operations import ResizeOperation


def test_resize_returns_photo_at_requested_dimensions() -> None:
    """Resize produces a new image while preserving the original photo."""
    original = Photo(Image.new("RGB", (4, 2), "red"))

    resized = ResizeOperation(2, 6).apply(original)

    assert resized.image.size == (2, 6)
    assert original.image.size == (4, 2)


@pytest.mark.parametrize("width,height", [(0, 1), (1, 0), (-1, 1), (1, -1)])
def test_resize_rejects_non_positive_dimensions(width: int, height: int) -> None:
    """Resize dimensions must be positive integers."""
    with pytest.raises(ValueError, match="positive integers"):
        ResizeOperation(width, height)


@pytest.mark.parametrize("width,height", [(1.5, 1), (1, 1.5), (True, 1)])
def test_resize_rejects_non_integer_dimensions(width: object, height: object) -> None:
    """Resize dimensions must be integer pixel counts."""
    with pytest.raises(ValueError, match="positive integers"):
        ResizeOperation(width, height)  # type: ignore[arg-type]
