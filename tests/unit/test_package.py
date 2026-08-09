"""Unit tests for package metadata."""

from piprints import __version__


def test_package_exposes_a_version() -> None:
    """Expose version metadata for callers and packaging tools."""
    assert __version__ == "0.1.0"
