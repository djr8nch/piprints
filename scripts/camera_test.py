#!/usr/bin/env python3
"""Capture a single image to validate a connected Raspberry Pi camera."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from piprints.camera import PiCamera


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the hardware validation capture."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("captures/camera-test.jpg"),
        help="Destination image path (default: captures/camera-test.jpg).",
    )
    return parser.parse_args()


def main() -> int:
    """Run a single camera capture and report the saved image path."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    arguments = parse_arguments()
    camera = PiCamera()

    try:
        camera.start()
        destination = camera.capture(arguments.output)
    finally:
        camera.stop()

    print(f"Captured test image: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
