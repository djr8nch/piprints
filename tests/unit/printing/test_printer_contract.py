"""Tests showing how application code consumes the printer boundary."""

from PIL import Image

from piprints.imaging import Photo
from piprints.printing import Printer, PrintResult
from tests.fakes import FakePrinter


def submit_photo(printer: Printer, photo: Photo) -> PrintResult:
    """Represent the eventual application dependency on the printer contract."""
    return printer.print_photo(photo)


def test_printer_contract_accepts_a_prepared_photo() -> None:
    """Printer adapters receive the final image without imaging coordination."""
    photo = Photo(Image.new("RGB", (2, 3), "black"))
    printer = FakePrinter()

    result = submit_photo(printer, photo)

    assert printer.print_requests == (photo,)
    assert result == PrintResult(job_id="fake-print-1")
