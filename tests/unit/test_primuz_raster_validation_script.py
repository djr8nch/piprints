"""Hardware-independent coverage for the manual PRIMUZ validation utility."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_validation_script() -> object:
    """Load the standalone script without executing its command-line entry point."""
    script_path = Path("scripts/validate_primuz_raster.py")
    spec = importlib.util.spec_from_file_location(
        "primuz_raster_validation", script_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_representative_layout_supports_the_validated_primuz_width() -> None:
    """Stage 3 can compose its in-memory layout before touching hardware."""
    module = _load_validation_script()

    photo = module._representative_layout(384)  # type: ignore[attr-defined]

    assert photo.image.size == (384, 1536)
