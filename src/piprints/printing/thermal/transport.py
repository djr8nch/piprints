"""Serial byte transport for future thermal-printer adapters."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self

from piprints.printing.exceptions import SerialTransportError

logger = logging.getLogger(__name__)


class SerialTransport(Protocol):
    """Open, write raw bytes to, and close one serial connection."""

    def open(self) -> None:
        """Open the configured serial connection."""

    def write(self, data: bytes) -> None:
        """Write all of ``data`` or raise a transport error."""

    def close(self) -> None:
        """Close the serial connection if it is open."""


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
