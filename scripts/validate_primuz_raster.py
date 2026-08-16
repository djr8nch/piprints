#!/usr/bin/env python3
"""Manually validate staged PRIMUZ raster printing through PiPrints.

This utility is intentionally not a test and is never run by CI.  Each
invocation submits exactly one image through the production PRIMUZ factory so
an operator can inspect the paper before progressing to the next stage.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from piprints.bootstrap import create_primuz_usb_printer
from piprints.imaging import Photo
from piprints.imaging.layouts import ClassicPhotoStripLayout
from piprints.printing import PrintError

DEFAULT_DEVICE_PATH = Path("/dev/usb/lp0")
_SMALL_PATTERN_SIZE = (64, 56)


def _draw_small_pattern() -> Photo:
    """Create an asymmetric, byte-aligned raster diagnostic image."""
    image = Image.new("RGB", _SMALL_PATTERN_SIZE, "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 7, 3), fill="black")
    draw.rectangle((0, 5, 15, 8), fill="black")
    draw.rectangle((0, 10, 23, 13), fill="black")
    draw.rectangle((0, 15, 63, 18), fill="black")
    draw.rectangle((56, 0, 63, 7), fill="black")
    draw.rectangle((60, 8, 63, 15), fill="black")
    draw.rectangle((48, 16, 55, 23), fill="black")
    for row in range(26, 42):
        for column in range(0, 64, 8):
            if (row - 26 + column // 8) % 2 == 0:
                draw.rectangle((column, row, column + 3, row), fill="black")
    draw.rectangle((4, 46, 11, 53), fill="black")
    draw.rectangle((20, 46, 27, 49), fill="black")
    draw.rectangle((36, 46, 43, 53), fill="black")
    draw.rectangle((52, 46, 59, 49), fill="black")
    return Photo(image)


def _draw_full_width_pattern(width: int) -> Photo:
    """Create a full-width raster image with visible edge and padding checks."""
    height = 160
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    marker_width = min(8, width)
    draw.rectangle((0, 0, marker_width - 1, 23), fill="black")
    draw.rectangle((width - marker_width, 0, width - 1, 23), fill="black")
    draw.rectangle((0, 32, width - 1, 39), fill="black")
    for y in range(48, 112):
        if y % 4 < 2:
            draw.rectangle((0, y, width // 3 - 1, y), fill="black")
        if y % 8 < 4:
            draw.rectangle((width * 2 // 3, y, width - 1, y), fill="black")
    for x in range(0, width, 16):
        draw.rectangle((x, 120, min(x + 7, width - 1), 143), fill="black")
    return Photo(image)


def _representative_layout(width: int) -> Photo:
    """Compose four synthetic source photos with PiPrints' strip layout."""
    # The strip's near-square cells need source height for its center-crop
    # strategy; square synthetic sources work for every supported head width.
    source_size = (width, width)
    photos: list[Photo] = []
    for index in range(4):
        image = Image.new("RGB", source_size, "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, source_size[0] // 2, source_size[1] - 1), fill="black")
        draw.rectangle(
            (index * source_size[0] // 4, 0, index * source_size[0] // 4 + 7, 15),
            fill="white",
        )
        draw.ellipse(
            (source_size[0] // 2, 8, source_size[0] - 9, source_size[1] - 9),
            fill=(48 + index * 48,) * 3,
        )
        photos.append(Photo(image))
    return ClassicPhotoStripLayout(
        canvas_width=width,
        canvas_height=width * 4,
        margin=8,
        gutter=4,
    ).compose(photos)


def _device_is_available(device_path: Path) -> bool:
    """Report normal-user device access without changing permissions."""
    if not device_path.exists():
        print(f"Device not found: {device_path}", file=sys.stderr)
        return False
    device_mode = stat.filemode(device_path.stat().st_mode)
    print(f"Device: {device_path} ({device_mode})")
    if not os.access(device_path, os.W_OK):
        print(
            "Current user cannot write to this device. Configure normal-user "
            "permissions; do not run PiPrints with sudo.",
            file=sys.stderr,
        )
        return False
    return True


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=Path, default=DEFAULT_DEVICE_PATH)
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument(
        "--printable-width",
        type=int,
        help="Verified/configured printable dot width; required for stages 2 and 3.",
    )
    parser.add_argument(
        "--confirm-stage-1",
        action="store_true",
        help="Record that Stage 1 paper output was physically inspected.",
    )
    parser.add_argument(
        "--confirm-stage-2",
        action="store_true",
        help="Record that Stage 2 paper output was physically inspected.",
    )
    return parser.parse_args()


def main() -> int:
    """Submit one selected validation image through the production factory."""
    arguments = _parse_arguments()
    if arguments.stage >= 2 and not arguments.confirm_stage_1:
        print(
            "Stage 2 requires a physically inspected Stage 1 result.",
            file=sys.stderr,
        )
        return 2
    if arguments.stage == 3 and not arguments.confirm_stage_2:
        print(
            "Stage 3 requires a physically inspected Stage 2 result.",
            file=sys.stderr,
        )
        return 2
    if arguments.stage >= 2 and (
        arguments.printable_width is None or arguments.printable_width < 16
    ):
        print(
            "Stages 2 and 3 require --printable-width of at least 16.",
            file=sys.stderr,
        )
        return 2
    if not _device_is_available(arguments.device):
        return 1

    if arguments.stage == 1:
        photo = _draw_small_pattern()
        description = (
            "Stage 1: expect left-growing top blocks, a full bar, a distinctive "
            "right-edge stepped mark, and asymmetric lower patterns."
        )
    elif arguments.stage == 2:
        photo = _draw_full_width_pattern(arguments.printable_width)
        description = (
            "Stage 2: expect solid markers at both paper edges, a full-width bar, "
            "unequal vertical patterns, alternating blocks, and white space."
        )
    else:
        photo = _representative_layout(arguments.printable_width)
        description = (
            "Stage 3: expect a four-photo PiPrints strip with distinct grayscale "
            "panels, circles, and a white marker in each panel."
        )

    print(description)
    print("Submitting exactly one raster image through create_primuz_usb_printer().")
    try:
        create_primuz_usb_printer(arguments.device).print_photo(photo)
    except PrintError as error:
        print(f"Print submission failed: {error}", file=sys.stderr)
        return 1
    print("Submission completed. Inspect the paper before running a later stage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
