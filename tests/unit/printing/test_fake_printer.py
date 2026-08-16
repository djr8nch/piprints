"""Unit tests for the deterministic printer test double."""

import pytest
from PIL import Image

from piprints.imaging import Photo
from piprints.printing import PrintError, PrintResult
from tests.fakes import FakePrinter


def make_photo(color: str) -> Photo:
    """Create a small prepared photo for printer interactions."""
    return Photo(Image.new("RGB", (2, 3), color))


def test_successful_print_records_the_submitted_photo() -> None:
    """A successful request is observable without real printer hardware."""
    photo = make_photo("red")
    printer = FakePrinter()

    result = printer.print_photo(photo)

    assert printer.print_count == 1
    assert printer.print_requests == (photo,)
    assert result == PrintResult(job_id="fake-print-1")


def test_multiple_successful_prints_preserve_request_order() -> None:
    """Higher-level tests can assert the order of submitted output images."""
    first_photo = make_photo("red")
    second_photo = make_photo("blue")
    printer = FakePrinter()

    first_result = printer.print_photo(first_photo)
    second_result = printer.print_photo(second_photo)

    assert printer.print_requests == (first_photo, second_photo)
    assert first_result == PrintResult(job_id="fake-print-1")
    assert second_result == PrintResult(job_id="fake-print-2")


def test_configured_failure_raises_print_error_without_recording() -> None:
    """Failure paths remain deterministic and do not simulate hardware details."""
    printer = FakePrinter(fail=True)

    with pytest.raises(PrintError, match="configured to fail"):
        printer.print_photo(make_photo("black"))

    assert printer.print_count == 0
    assert printer.print_requests == ()
