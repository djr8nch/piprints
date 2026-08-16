"""Tests for the pre-hardware-validation PRIMUZ printer adapter."""

import pytest
from PIL import Image

from piprints.imaging import Photo
from piprints.printing import Printer, PrintError, PrintResult, SerialTransportError
from piprints.printing.thermal import PrimuzThermalPrinter, ThermalRasterEncoder


class RecordingTransport:
    """Record serial-transport calls without opening a serial connection."""

    def __init__(
        self,
        *,
        write_error: SerialTransportError | None = None,
        close_error: SerialTransportError | None = None,
    ) -> None:
        self.write_error = write_error
        self.close_error = close_error
        self.calls: list[str] = []
        self.writes: list[bytes] = []

    def open(self) -> None:
        """Record opening the injected transport."""
        self.calls.append("open")

    def write(self, data: bytes) -> None:
        """Record one raw write or raise a configured transport error."""
        self.calls.append("write")
        if self.write_error is not None:
            raise self.write_error
        self.writes.append(data)

    def close(self) -> None:
        """Record closing the injected transport."""
        self.calls.append("close")
        if self.close_error is not None:
            raise self.close_error


def submit_photo(printer: Printer, photo: Photo) -> PrintResult:
    """Exercise structural use through the public printer contract."""
    return printer.print_photo(photo)


def test_printer_frames_and_sends_one_raster_command() -> None:
    """One prepared 8-dot image becomes one assumed ESC/POS raster command."""
    transport = RecordingTransport()
    printer = PrimuzThermalPrinter(transport, ThermalRasterEncoder())

    result = submit_photo(printer, Photo(Image.new("RGB", (8, 1), "black")))

    assert result == PrintResult()
    assert transport.calls == ["open", "write", "close"]
    assert transport.writes == [b"\x1d\x76\x30\x00\x01\x00\x01\x00\xff"]


def test_printer_uses_encoded_row_major_raster_data_once() -> None:
    """The adapter forwards the encoder's bytes without duplicate image writes."""
    image = Image.new("RGB", (8, 2), "white")
    image.putpixel((0, 0), (0, 0, 0))
    image.putpixel((7, 1), (0, 0, 0))
    transport = RecordingTransport()
    printer = PrimuzThermalPrinter(transport, ThermalRasterEncoder())

    printer.print_photo(Photo(image))

    assert transport.writes == [b"\x1d\x76\x30\x00\x01\x00\x02\x00\x80\x01"]
    assert len(transport.writes) == 1


def test_transport_failure_becomes_a_printer_error_and_closes() -> None:
    """Transport details do not leak through the public printer boundary."""
    transport_error = SerialTransportError("serial cable disconnected")
    transport = RecordingTransport(write_error=transport_error)
    printer = PrimuzThermalPrinter(transport, ThermalRasterEncoder())

    with pytest.raises(PrintError) as error_info:
        printer.print_photo(Photo(Image.new("RGB", (8, 1), "black")))

    assert error_info.value.__cause__ is transport_error
    assert transport.calls == ["open", "write", "close"]
    assert transport.writes == []


def test_close_failure_becomes_a_printer_error_after_sending_raster() -> None:
    """A failed transport cleanup is not reported as successful printing."""
    close_error = SerialTransportError("serial port did not close")
    transport = RecordingTransport(close_error=close_error)
    printer = PrimuzThermalPrinter(transport, ThermalRasterEncoder())

    with pytest.raises(PrintError) as error_info:
        printer.print_photo(Photo(Image.new("RGB", (8, 1), "black")))

    assert error_info.value.__cause__ is close_error
    assert transport.calls == ["open", "write", "close"]
    assert len(transport.writes) == 1


def test_encoder_failure_does_not_open_or_write_the_transport() -> None:
    """Printer-width preparation errors occur before serial communication."""
    transport = RecordingTransport()
    printer = PrimuzThermalPrinter(transport, ThermalRasterEncoder(max_width=8))

    with pytest.raises(PrintError, match="prepare photo"):
        printer.print_photo(Photo(Image.new("RGB", (9, 1), "black")))

    assert transport.calls == []
    assert transport.writes == []
