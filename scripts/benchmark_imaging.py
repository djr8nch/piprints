"""Measure deterministic in-memory imaging operations on reference hardware."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from time import perf_counter

from PIL import Image

from piprints.imaging import (
    AspectRatio,
    CenterCropAspectRatioStrategy,
    Photo,
    PhotoPipeline,
)
from piprints.imaging.layouts import SinglePhotoLayout
from piprints.imaging.operations import CropOperation, ResizeOperation

_TARGET_RATIO = AspectRatio(2, 3)
_OUTPUT_SIZE = (1200, 1800)
_SCENARIOS = ((1920, 1080), (4608, 2592))


def main() -> int:
    """Run image-operation timing samples without requiring camera hardware."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="number of samples per operation and image size (default: 3)",
    )
    arguments = parser.parse_args()
    if arguments.repetitions <= 0:
        parser.error("--repetitions must be positive")

    for width, height in _SCENARIOS:
        _run_scenario(width, height, arguments.repetitions)
    return 0


def _run_scenario(width: int, height: int, repetitions: int) -> None:
    """Print timing measurements for one generated RGB source image."""
    photo = Photo(Image.new("RGB", (width, height), "gray"))
    strategy = CenterCropAspectRatioStrategy()
    crop_box = strategy.crop_box(width, height, _TARGET_RATIO)
    crop = CropOperation(crop_box)
    resize = ResizeOperation(*_OUTPUT_SIZE)
    pipeline = PhotoPipeline([crop, resize])
    layout = SinglePhotoLayout()

    print(f"\n{width}x{height} RGB source; {repetitions} samples")
    _measure(
        "center-crop calculation",
        lambda: strategy.crop_box(width, height, _TARGET_RATIO),
        repetitions,
    )
    _measure("crop operation", lambda: crop.apply(photo), repetitions)
    _measure("resize operation", lambda: resize.apply(photo), repetitions)
    _measure("crop + resize pipeline", lambda: pipeline.process(photo), repetitions)
    _measure(
        "single-photo imaging pipeline",
        lambda: layout.compose([pipeline.process(photo)]),
        repetitions,
    )


def _measure(name: str, operation: Callable[[], object], repetitions: int) -> None:
    """Run an operation repeatedly and print mean elapsed milliseconds."""
    elapsed_seconds = 0.0
    for _ in range(repetitions):
        start = perf_counter()
        operation()
        elapsed_seconds += perf_counter() - start
    print(f"  {name}: {(elapsed_seconds / repetitions) * 1000:.2f} ms mean")


if __name__ == "__main__":
    raise SystemExit(main())
