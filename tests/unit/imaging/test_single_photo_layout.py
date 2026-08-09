"""Unit tests for the initial layout strategy."""

from __future__ import annotations

import pytest
from PIL import Image

from piprints.imaging import InvalidPhotoCountError, Photo
from piprints.imaging.layouts import SinglePhotoLayout


def make_photo() -> Photo:
    """Create a small layout input photo."""
    return Photo(Image.new("RGB", (1, 1), "black"))


def test_single_photo_layout_requires_one_photo() -> None:
    """The current layout declares one required capture."""
    assert SinglePhotoLayout().required_photos == 1


def test_single_photo_layout_returns_the_sole_photo() -> None:
    """One processed photo is a valid final composition."""
    photo = make_photo()

    assert SinglePhotoLayout().compose([photo]) is photo


@pytest.mark.parametrize("photos", [[], [make_photo(), make_photo()]])
def test_single_photo_layout_rejects_wrong_photo_count(photos: list[Photo]) -> None:
    """The layout reports an imaging-owned error for invalid input counts."""
    with pytest.raises(InvalidPhotoCountError, match="exactly one photo"):
        SinglePhotoLayout().compose(photos)
