"""Unit tests for the concrete multi-photo layout strategies."""

from __future__ import annotations

import pytest
from PIL import Image

from piprints.imaging import InvalidPhotoCountError, Photo
from piprints.imaging.layouts import ClassicPhotoStripLayout, FourPhotoLayout


def make_photo(color: str, size: tuple[int, int]) -> Photo:
    """Create a solid input image whose placement is easy to assert."""
    return Photo(Image.new("RGB", size, color))


def test_four_photo_layout_composes_ordered_grid_cells() -> None:
    """Four source photos occupy deterministic top-left to bottom-right cells."""
    layout = FourPhotoLayout(canvas_width=44, canvas_height=44, margin=2, gutter=2)
    result = layout.compose(
        [
            make_photo("red", (38, 38)),
            make_photo("green", (38, 38)),
            make_photo("blue", (38, 38)),
            make_photo("yellow", (38, 38)),
        ]
    )

    assert result.image.size == (44, 44)
    assert result.image.getpixel((2, 2)) == (255, 0, 0)
    assert result.image.getpixel((23, 2)) == (0, 128, 0)
    assert result.image.getpixel((2, 23)) == (0, 0, 255)
    assert result.image.getpixel((23, 23)) == (255, 255, 0)
    assert result.image.getpixel((0, 0)) == (255, 255, 255)
    assert result.image.tobytes() == layout.compose(
        [
            make_photo("red", (38, 38)),
            make_photo("green", (38, 38)),
            make_photo("blue", (38, 38)),
            make_photo("yellow", (38, 38)),
        ]
    ).image.tobytes()


def test_classic_photo_strip_composes_ordered_vertical_cells() -> None:
    """Four source photos occupy deterministic top-to-bottom strip cells."""
    layout = ClassicPhotoStripLayout(
        canvas_width=30, canvas_height=54, margin=2, gutter=2
    )
    result = layout.compose(
        [
            make_photo("red", (52, 22)),
            make_photo("green", (52, 22)),
            make_photo("blue", (52, 22)),
            make_photo("yellow", (52, 22)),
        ]
    )

    assert result.image.size == (30, 54)
    assert [result.image.getpixel((2, y)) for y in (2, 15, 28, 41)] == [
        (255, 0, 0),
        (0, 128, 0),
        (0, 0, 255),
        (255, 255, 0),
    ]


@pytest.mark.parametrize("layout", [FourPhotoLayout(), ClassicPhotoStripLayout()])
def test_multi_photo_layout_rejects_wrong_photo_count(
    layout: FourPhotoLayout | ClassicPhotoStripLayout,
) -> None:
    """Concrete layouts enforce their declared strategy contract."""
    with pytest.raises(InvalidPhotoCountError, match="exactly four photos"):
        layout.compose([make_photo("black", (100, 100))])


def test_four_photo_layout_rejects_geometry_without_equal_cells() -> None:
    """Cell dimensions cannot silently round and create uneven composition."""
    with pytest.raises(ValueError, match="whole-pixel"):
        FourPhotoLayout(canvas_width=45, canvas_height=44, margin=2, gutter=2)
