"""Tests for the theme-selection metadata boundary."""

import pytest

from piprints.themes import ThemeCatalog, ThemeOption


def test_catalog_exposes_only_currently_usable_theme_options() -> None:
    """Unavailable options never reach a selection widget."""
    catalog = ThemeCatalog(
        (
            ThemeOption("classic", "Classic"),
            ThemeOption("wedding", "Wedding", available=False),
        )
    )

    assert catalog.options == (ThemeOption("classic", "Classic"),)
    assert catalog.default_identifier == "classic"
    assert catalog.contains("classic")
    assert not catalog.contains("wedding")


def test_catalog_requires_at_least_one_usable_theme() -> None:
    """The application cannot begin a session with no valid theme selection."""
    with pytest.raises(ValueError, match="at least one usable theme"):
        ThemeCatalog((ThemeOption("unavailable", "Unavailable", available=False),))
