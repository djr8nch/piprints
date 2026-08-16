"""Byte transports for thermal-printer adapters."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Protocol, Self

from piprints.printing.exceptions import (
    SerialTransportError,
    UsbPrinterTransportError,
)

logger = logging.getLogger(__name__)


class PrinterTransport(Protocol):
    """Open, write raw bytes to, and close one printer connection."""

    def open(self) -> None:
        """Open the configured serial connection."""

    def write(self, data: bytes) -> None:
        """Write all of ``data`` or raise a transport error."""

    def close(self) -> None:
        """Close the printer connection if it is open."""


class SerialTransport(PrinterTransport, Protocol):
    """Legacy name for the serial implementation's byte-transport contract."""


class _SerialConnection(Protocol):
    """The pyserial connection behavior used by this transport."""

    def write(self, data: bytes) -> int:
        """Write bytes and return the number accepted by the connection."""

    def close(self) -> None:
        """Close the connection."""


class _SerialFactory(Protocol):
    """Create a serial connection from PiPrints serial settings."""

    def __call__(
        self, port: str, *, baudrate: int, timeout: float | None
    ) -> _SerialConnection:
        """Open and return a serial connection."""


class _UsbPrinterFile(Protocol):
    """The binary file behavior used by the USB printer transport."""

    def write(self, data: bytes) -> int:
        """Write bytes and return the number accepted by the device."""

    def flush(self) -> None:
        """Flush buffered bytes to the device."""

    def close(self) -> None:
        """Close the device file."""


class _UsbPrinterFileFactory(Protocol):
    """Open a configured Linux USB printer character device."""

    def __call__(self, path: str, mode: str) -> _UsbPrinterFile:
        """Return a writable binary device file."""


@dataclass(frozen=True)
class SerialTransportSettings:
    """Injected serial connection configuration for a thermal printer."""

    port: str
    baud_rate: int
    timeout: float | None = 1.0

    def __post_init__(self) -> None:
        """Reject invalid configuration before a hardware connection is opened."""
        if not isinstance(self.port, str) or not self.port:
            raise ValueError("Serial port must be a non-empty string.")
        if (
            isinstance(self.baud_rate, bool)
            or not isinstance(self.baud_rate, int)
            or self.baud_rate <= 0
        ):
            raise ValueError("Serial baud rate must be a positive integer.")
        if (
            self.timeout is not None
            and (
                isinstance(self.timeout, bool)
                or not isinstance(self.timeout, int | float)
                or self.timeout < 0
            )
        ):
            raise ValueError("Serial timeout must be non-negative seconds or None.")


def _open_usb_printer_file(path: str, mode: str) -> BinaryIO:
    """Open a Linux printer-class character device in binary write mode."""
    return open(path, mode)


def _open_pyserial(
    port: str, *, baudrate: int, timeout: float | None
) -> _SerialConnection:
    """Open a pyserial connection without exposing the dependency elsewhere."""
    try:
        import serial
    except ImportError as error:
        raise SerialTransportError(
            "pyserial is unavailable. Reinstall PiPrints with its dependencies."
        ) from error
    return serial.Serial(port=port, baudrate=baudrate, timeout=timeout)


class PySerialTransport:
    """Transport raw bytes through one pyserial connection.

    The optional factory isolates pyserial and physical serial devices from
    unit tests. Future thermal-printer adapters own command framing and pass
    only already-framed bytes to this transport.
    """

    def __init__(
        self,
        settings: SerialTransportSettings,
        *,
        serial_factory: _SerialFactory = _open_pyserial,
    ) -> None:
        self._settings = settings
        self._serial_factory = serial_factory
        self._connection: _SerialConnection | None = None

    def __enter__(self) -> Self:
        """Open this transport for use in a ``with`` block."""
        self.open()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Close the connection, preserving any exception from the block."""
        if exception_type is None:
            self.close()
        else:
            try:
                self.close()
            except SerialTransportError:
                logger.exception("Unable to close serial transport during cleanup")
        return False

    def open(self) -> None:
        """Open the configured connection once."""
        if self._connection is not None:
            return
        try:
            self._connection = self._serial_factory(
                self._settings.port,
                baudrate=self._settings.baud_rate,
                timeout=self._settings.timeout,
            )
        except SerialTransportError:
            raise
        except Exception as error:
            raise SerialTransportError(
                f"Unable to open serial port {self._settings.port}."
            ) from error

    def write(self, data: bytes) -> None:
        """Write every byte in ``data`` to the open serial connection."""
        connection = self._connection
        if connection is None:
            raise SerialTransportError("Serial transport must be open before writing.")
        try:
            written = connection.write(data)
        except Exception as error:
            raise SerialTransportError(
                "Unable to write to serial transport."
            ) from error
        if written != len(data):
            raise SerialTransportError(
                f"Serial transport wrote {written} of {len(data)} bytes."
            )

    def close(self) -> None:
        """Close and discard the current connection."""
        connection = self._connection
        if connection is None:
            return
        self._connection = None
        try:
            connection.close()
        except Exception as error:
            raise SerialTransportError("Unable to close serial transport.") from error


class UsbPrinterTransport:
    """Transport raw bytes to a Linux USB printer-class device node.

    A device file is opened for each printer operation and closed immediately
    afterwards. This mirrors the existing printer adapter lifecycle and avoids
    retaining a stale handle if a USB printer is disconnected between jobs.
    """

    def __init__(
        self,
        device_path: str | Path,
        *,
        file_factory: _UsbPrinterFileFactory = _open_usb_printer_file,
    ) -> None:
        if not isinstance(device_path, str | Path):
            raise ValueError("USB printer device path must be a non-empty path.")
        path = str(device_path)
        if not path:
            raise ValueError("USB printer device path must be a non-empty string.")
        self._device_path = path
        self._file_factory = file_factory
        self._file: _UsbPrinterFile | None = None

    def open(self) -> None:
        """Open the configured USB printer device once."""
        if self._file is not None:
            return
        try:
            self._file = self._file_factory(self._device_path, "wb")
        except Exception as error:
            raise UsbPrinterTransportError(
                f"Unable to open USB printer device {self._device_path}."
            ) from error

    def write(self, data: bytes) -> None:
        """Write all bytes to the currently open USB printer device."""
        device_file = self._file
        if device_file is None:
            raise UsbPrinterTransportError(
                "USB printer transport must be open before writing."
            )

        remaining = data
        try:
            while remaining:
                written = device_file.write(remaining)
                if written is None or not 0 < written <= len(remaining):
                    raise OSError("USB printer device accepted no bytes.")
                remaining = remaining[written:]
            device_file.flush()
        except Exception as error:
            raise UsbPrinterTransportError(
                f"Unable to write to USB printer device {self._device_path}."
            ) from error

    def close(self) -> None:
        """Close and discard the current USB printer device file."""
        device_file = self._file
        if device_file is None:
            return
        self._file = None
        try:
            device_file.close()
        except Exception as error:
            raise UsbPrinterTransportError(
                f"Unable to close USB printer device {self._device_path}."
            ) from error
