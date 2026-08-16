"""PRIMUZ MC206H thermal-printer adapter; raster validation remains pending."""

from __future__ import annotations

import logging

from piprints.imaging import Photo
from piprints.printing.exceptions import PrintError, PrinterTransportError
from piprints.printing.models import PrintResult
from piprints.printing.thermal.raster import ThermalRaster, ThermalRasterEncoder
from piprints.printing.thermal.transport import PrinterTransport

logger = logging.getLogger(__name__)

# RASTER-VALIDATION ASSUMPTION: USB raw ESC/POS text output is physically
# validated, but no manufacturer command manual is available to this project.
# These bytes use the ESC/POS GS v 0 raster-image format documented by Epson.
# PRIMUZ raster compatibility still requires physical validation.
_ESC_POS_RASTER_PREFIX = b"\x1d\x76\x30"
_NORMAL_RASTER_MODE = 0
_MAX_16_BIT_VALUE = 0xFFFF


class PrimuzThermalPrinter:
    """Submit prepared photos through assumed PRIMUZ ESC/POS raster framing.

    This adapter is intentionally limited to one raster-print command. It does
    not initialize, feed, cut, or delay because those command details have not
    been verified for the PRIMUZ MC206H hardware.
    """

    def __init__(
        self, transport: PrinterTransport, raster_encoder: ThermalRasterEncoder
    ) -> None:
        self._transport = transport
        self._raster_encoder = raster_encoder

    def print_photo(self, photo: Photo) -> PrintResult:
        """Encode and submit one photo using the assumed raster command format."""
        try:
            raster = self._raster_encoder.encode(photo)
            command = _raster_print_command(raster)
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
    """Frame one raster with the assumed ESC/POS GS v 0 command.

    The command format is ``GS v 0 m xL xH yL yH d...``. ``x`` is bytes per
    row and ``y`` is rows, both encoded little-endian. Its PRIMUZ compatibility
    is an explicit pre-hardware-validation assumption.
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
