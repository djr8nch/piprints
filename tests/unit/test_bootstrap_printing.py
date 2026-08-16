"""Tests for optional printer composition at the application boundary."""

from pathlib import Path

from piprints.bootstrap import create_primuz_usb_printer
from piprints.printing.thermal import PrimuzThermalPrinter


def test_primuz_usb_factory_creates_a_printer_without_opening_the_device() -> None:
    """Composition selects USB explicitly while keeping hardware lazy."""
    printer = create_primuz_usb_printer(Path("/dev/usb/lp-test"))

    assert isinstance(printer, PrimuzThermalPrinter)
