"""Tests showing how application code consumes the printer boundary."""

from PIL import Image

from piprints.imaging import Photo
from piprints.printing import Printer, PrintResult


class RecordingPrinter:
    """Small hardware-free adapter used to exercise the public contract."""

    def __init__(self) -> None:
        self.photos: list[Photo] = []

    def print_photo(self, photo: Photo) -> PrintResult:
        """Record a prepared photo as an accepted print submission."""
        self.photos.append(photo)
        return PrintResult(job_id="test-job")


def submit_photo(printer: Printer, photo: Photo) -> PrintResult:
    """Represent the eventual application dependency on the printer contract."""
    return printer.print_photo(photo)


def test_printer_contract_accepts_a_prepared_photo() -> None:
    """Printer adapters receive the final image without imaging coordination."""
    photo = Photo(Image.new("RGB", (2, 3), "black"))
    printer = RecordingPrinter()

    result = submit_photo(printer, photo)

    assert printer.photos == [photo]
    assert result == PrintResult(job_id="test-job")
