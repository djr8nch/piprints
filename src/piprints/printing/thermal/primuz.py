"""PRIMUZ MC206H thermal-printer adapter."""

from __future__ import annotations

import logging

from piprints.imaging import Photo
from piprints.printing.exceptions import PrintError, PrinterTransportError
from piprints.printing.models import PrintResult
from piprints.printing.thermal.raster import ThermalRaster, ThermalRasterEncoder
from piprints.printing.thermal.transport import PrinterTransport

logger = logging.getLogger(__name__)

# The PRIMUZ MC206H accepts this ESC/POS GS v 0 raster framing on the validated
# USB / usblp path. The command format remains documented by Epson.
_ESC_POS_RASTER_PREFIX = b"\x1d\x76\x30"
_NORMAL_RASTER_MODE = 0
_MAX_16_BIT_VALUE = 0xFFFF
_DEFAULT_BOTTOM_MARGIN_DOTS = 32


class PrimuzThermalPrinter:
    """Submit prepared photos through validated PRIMUZ ESC/POS raster framing.

    A small white raster margin follows each image so an operator has room to
    tear the paper. This uses the same validated ``GS v 0`` raster command,
    rather than adding an unverified device-specific feed command.
    """

    def __init__(
        self,
        transport: PrinterTransport,
        raster_encoder: ThermalRasterEncoder,
        *,
        bottom_margin_dots: int = _DEFAULT_BOTTOM_MARGIN_DOTS,
    ) -> None:
        if (
            isinstance(bottom_margin_dots, bool)
            or not isinstance(bottom_margin_dots, int)
            or bottom_margin_dots < 0
        ):
            raise ValueError("Bottom raster margin must be a non-negative integer.")
        self._transport = transport
        self._raster_encoder = raster_encoder
        self._bottom_margin_dots = bottom_margin_dots

    def print_photo(self, photo: Photo) -> PrintResult:
        """Encode and submit one photo using the assumed raster command format."""
        try:
            raster = self._raster_encoder.encode(photo)
            command = _raster_print_command(
                _with_bottom_margin(raster, self._bottom_margin_dots)
            )
        except ValueError as error:
            raise PrintError("Unable to prepare photo for PRIMUZ printing.") from error

        try:
            self._transport.open()
            self._transport.write(command)
        except PrinterTransportError as error:
            self._close_after_transport_failure()
            raise PrintError("Unable to submit photo to the PRIMUZ printer.") from error

        try:
            self._transport.close()
        except PrinterTransportError as error:
            raise PrintError("Unable to close the PRIMUZ printer transport.") from error

        logger.info("Submitted one raster image to the PRIMUZ printer")
        return PrintResult()

    def _close_after_transport_failure(self) -> None:
        """Attempt cleanup while preserving the original transport failure."""
        try:
            self._transport.close()
        except PrinterTransportError:
            logger.exception("Unable to close PRIMUZ transport after print failure")


def _raster_print_command(raster: ThermalRaster) -> bytes:
    """Frame one raster with the validated ESC/POS GS v 0 command.

    The command format is ``GS v 0 m xL xH yL yH d...``. ``x`` is bytes per
    row and ``y`` is rows, both encoded little-endian.
    """
    if not 0 < raster.bytes_per_row <= _MAX_16_BIT_VALUE:
        raise ValueError("Thermal raster bytes per row must fit in 16 bits.")
    if not 0 < raster.height <= _MAX_16_BIT_VALUE:
        raise ValueError("Thermal raster height must fit in 16 bits.")
    expected_data_length = raster.bytes_per_row * raster.height
    if len(raster.data) != expected_data_length:
        raise ValueError(
            "Thermal raster data length must match its row width and height."
        )

    return (
        _ESC_POS_RASTER_PREFIX
        + bytes([_NORMAL_RASTER_MODE])
        + raster.bytes_per_row.to_bytes(2, byteorder="little")
        + raster.height.to_bytes(2, byteorder="little")
        + raster.data
    )


def _with_bottom_margin(raster: ThermalRaster, margin_dots: int) -> ThermalRaster:
    """Append white raster rows to provide a physical tear margin."""
    padded_height = raster.height + margin_dots
    if padded_height > _MAX_16_BIT_VALUE:
        raise ValueError("Thermal raster height including margin must fit in 16 bits.")
    return ThermalRaster(
        data=raster.data + bytes(raster.bytes_per_row * margin_dots),
        width=raster.width,
        height=padded_height,
        bytes_per_row=raster.bytes_per_row,
    )
