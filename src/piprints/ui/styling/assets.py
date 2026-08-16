"""Resolve packaged visual assets for the PySide6 presentation layer."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def logo_path() -> Path:
    """Return the packaged PiPrints logo path for Qt image loading.

    UI assets live beside the UI package so a runtime installation never needs
    to reach into documentation files. Setuptools installs these resources as
    normal package files, which Qt can load directly from this path.
    """
    return Path(str(files("piprints.ui").joinpath("assets", "logos", "logo.png")))
