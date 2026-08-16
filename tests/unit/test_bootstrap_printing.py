"""Tests for optional printer composition at the application boundary."""

from pathlib import Path

import pytest
from PIL import Image

from piprints.bootstrap import create_primuz_usb_printer
from piprints.imaging import Photo
from piprints.printing import PrintError
from piprints.printing.thermal import PrimuzThermalPrinter


def test_primuz_usb_factory_creates_a_printer_without_opening_the_device() -> None:
    """Composition selects USB explicitly while keeping hardware lazy."""
    printer = create_primuz_usb_printer(Path("/dev/usb/lp-test"))

    assert isinstance(printer, PrimuzThermalPrinter)


def test_primuz_usb_factory_rejects_images_wider_than_validated_head() -> None:
    """MC206H composition refuses raster data beyond the 384-dot print head."""
    printer = create_primuz_usb_printer("/dev/usb/lp-test")

    with pytest.raises(PrintError, match="Unable to prepare"):
        printer.print_photo(Photo(Image.new("RGB", (385, 1), "black")))
