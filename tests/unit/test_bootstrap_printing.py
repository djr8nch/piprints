"""Tests for optional printer composition at the application boundary."""

import subprocess
import sys
from pathlib import Path

import pytest

import piprints.bootstrap as bootstrap
from piprints.bootstrap import create_primuz_usb_printer, create_production_printer
from piprints.printing.thermal import PrimuzThermalPrinter
from tests.fakes import FakePrinter


def test_printer_factory_import_does_not_load_qt_widgets() -> None:
    """Headless printer composition must not require Qt graphics libraries."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from piprints.bootstrap import create_primuz_usb_printer; "
                "assert 'PySide6.QtWidgets' not in sys.modules; "
                "create_primuz_usb_printer('/dev/usb/lp-test')"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_primuz_usb_factory_creates_a_printer_without_opening_the_device() -> None:
    """Composition selects USB explicitly while keeping hardware lazy."""
    printer = create_primuz_usb_printer(Path("/dev/usb/lp-test"))

    assert isinstance(printer, PrimuzThermalPrinter)


def test_production_bootstrap_wires_the_validated_primuz_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hardware selection remains localized to the composition root."""
    printer = FakePrinter()
    factory_paths: list[Path] = []
    monkeypatch.setattr(bootstrap, "_is_usable_printer_device", lambda _path: True)
    monkeypatch.setattr(
        bootstrap,
        "create_primuz_usb_printer",
        lambda path: factory_paths.append(Path(path)) or printer,
    )

    assert create_production_printer() is printer
    assert factory_paths == [Path("/dev/usb/lp0")]


def test_production_bootstrap_keeps_digital_only_mode_when_device_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing printer device does not prevent normal application startup."""
    monkeypatch.setattr(bootstrap, "_is_usable_printer_device", lambda _path: False)

    assert create_production_printer() is None
