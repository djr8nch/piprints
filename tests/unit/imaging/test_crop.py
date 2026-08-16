"""Unit tests for explicit pixel cropping."""

from __future__ import annotations

import pytest
from PIL import Image

from piprints.imaging import CropBox, InvalidCropError, Photo
from piprints.imaging.operations import CropOperation


def test_crop_returns_selected_region_without_mutating_source() -> None:
    """Crop keeps the expected source pixels in a new photo."""
    image = Image.new("RGB", (4, 2), "black")
    image.putpixel((1, 0), (255, 0, 0))
    image.putpixel((2, 1), (0, 255, 0))
    original = Photo(image)

    cropped = CropOperation(CropBox(1, 0, 3, 2)).apply(original)

    assert cropped.image.size == (2, 2)
    assert cropped.image.getpixel((0, 0)) == (255, 0, 0)
    assert cropped.image.getpixel((1, 1)) == (0, 255, 0)
    assert original.image.size == (4, 2)
    assert original.image.getpixel((0, 0)) == (0, 0, 0)


@pytest.mark.parametrize(
    "coordinates",
    [(-1, 0, 1, 1), (0, -1, 1, 1), (1, 0, 1, 1), (0, 1, 1, 1)],
)
def test_crop_box_rejects_invalid_coordinates(
    coordinates: tuple[int, int, int, int],
) -> None:
    """Crop boxes must be non-negative and have positive dimensions."""
    with pytest.raises(InvalidCropError):
        CropBox(*coordinates)


def test_crop_rejects_region_outside_photo_bounds() -> None:
    """Cropping cannot request pixels outside the source photo."""
    photo = Photo(Image.new("RGB", (2, 2), "black"))

    with pytest.raises(InvalidCropError, match="exceed"):
        CropOperation(CropBox(0, 0, 3, 2)).apply(photo)
