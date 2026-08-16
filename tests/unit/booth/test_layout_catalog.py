"""Tests for the application-level layout selection boundary."""

from __future__ import annotations

import pytest

from piprints.booth import LayoutCatalog, LayoutOption
from piprints.imaging.layouts import FourPhotoLayout, SinglePhotoLayout


def test_catalog_exposes_descriptors_and_creates_the_selected_strategy() -> None:
    """The application model does not require UI access to concrete layouts."""
    single = LayoutOption("single", "Single", "1 photo", 1, 1, 1)
    grid = LayoutOption("grid", "Grid", "4 photos", 4, 2, 2)
    catalog = LayoutCatalog(
        (single, grid),
        {"single": SinglePhotoLayout, "grid": FourPhotoLayout},
    )

    selected = catalog.create("grid")

    assert catalog.options == (single, grid)
    assert isinstance(selected, FourPhotoLayout)
    assert selected.required_photos == grid.required_photos


def test_catalog_rejects_options_that_do_not_match_their_strategy() -> None:
    """A bad descriptor cannot create a session with the wrong capture count."""
    option = LayoutOption("single", "Single", "4 photos", 4, 1, 1)
    catalog = LayoutCatalog((option,), {"single": SinglePhotoLayout})

    with pytest.raises(ValueError, match="requires 1 photos"):
        catalog.create("single")
