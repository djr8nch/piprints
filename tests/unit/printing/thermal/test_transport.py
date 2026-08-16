"""Unit tests for pyserial-backed thermal-printer byte transport."""

import pytest

from piprints.printing import SerialTransportError
from piprints.printing.thermal import PySerialTransport, SerialTransportSettings


class FakeSerialConnection:
    """Record raw serial interactions without opening a physical device."""

    def __init__(
        self,
        *,
        write_error: Exception | None = None,
        close_error: Exception | None = None,
        write_count: int | None = None,
    ) -> None:
        self.write_error = write_error
        self.close_error = close_error
        self.write_count = write_count
        self.writes: list[bytes] = []
        self.close_calls = 0

    def write(self, data: bytes) -> int:
        """Record bytes or raise the configured write failure."""
        if self.write_error is not None:
            raise self.write_error
        self.writes.append(data)
        return self.write_count if self.write_count is not None else len(data)

    def close(self) -> None:
        """Record closing or raise the configured close failure."""
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error


class RecordingSerialFactory:
    """Return one injected connection and record its requested configuration."""

    def __init__(self, connection: FakeSerialConnection) -> None:
        self.connection = connection
        self.calls: list[tuple[str, int, float | None]] = []

    def __call__(
        self, port: str, *, baudrate: int, timeout: float | None
    ) -> FakeSerialConnection:
        """Record configuration without interacting with a serial device."""
        self.calls.append((port, baudrate, timeout))
        return self.connection


def make_settings() -> SerialTransportSettings:
    """Create deterministic serial configuration for transport tests."""
    return SerialTransportSettings("/dev/ttyTEST0", baud_rate=19_200, timeout=2.5)


def test_open_passes_injected_serial_configuration_to_factory() -> None:
    """Configured device, baud rate, and timeout remain transport concerns."""
    factory = RecordingSerialFactory(FakeSerialConnection())
    transport = PySerialTransport(make_settings(), serial_factory=factory)

    transport.open()

    assert factory.calls == [("/dev/ttyTEST0", 19_200, 2.5)]


def test_write_transmits_raw_bytes_and_close_releases_connection() -> None:
    """The transport writes exact bytes and supports idempotent cleanup."""
    connection = FakeSerialConnection()
    transport = PySerialTransport(
        make_settings(), serial_factory=RecordingSerialFactory(connection)
    )

    transport.open()
    transport.write(b"\x01\x02")
    transport.close()
    transport.close()

    assert connection.writes == [b"\x01\x02"]
    assert connection.close_calls == 1


def test_context_manager_closes_after_an_exception() -> None:
    """Cleanup closes the serial connection while preserving the block error."""
    connection = FakeSerialConnection()
    transport = PySerialTransport(
        make_settings(), serial_factory=RecordingSerialFactory(connection)
    )

    with pytest.raises(RuntimeError, match="operation failed"):
        with transport:
            raise RuntimeError("operation failed")

    assert connection.close_calls == 1


def test_write_failure_is_translated_and_context_cleanup_closes_connection() -> None:
    """Low-level write failures preserve their cause and never leak resources."""
    write_error = OSError("device disconnected")
    connection = FakeSerialConnection(write_error=write_error)
    transport = PySerialTransport(
        make_settings(), serial_factory=RecordingSerialFactory(connection)
    )

    with pytest.raises(SerialTransportError) as error_info:
        with transport:
            transport.write(b"print data")

    assert error_info.value.__cause__ is write_error
    assert connection.close_calls == 1


def test_partial_write_raises_a_transport_error() -> None:
    """A transport cannot silently report a partial raw-byte write as success."""
    connection = FakeSerialConnection(write_count=1)
    transport = PySerialTransport(
        make_settings(), serial_factory=RecordingSerialFactory(connection)
    )

    transport.open()
    with pytest.raises(SerialTransportError, match="wrote 1 of 2 bytes"):
        transport.write(b"\x01\x02")


def test_write_requires_an_open_transport() -> None:
    """Callers receive a domain error instead of an attribute failure."""
    transport = PySerialTransport(
        make_settings(), serial_factory=RecordingSerialFactory(FakeSerialConnection())
    )

    with pytest.raises(SerialTransportError, match="must be open"):
        transport.write(b"print data")


@pytest.mark.parametrize(
    "port,baud_rate,timeout",
    [("", 9_600, 1.0), ("/dev/ttyX", 0, 1.0), ("/dev/ttyX", 9_600, -1.0)],
)
def test_settings_reject_invalid_connection_values(
    port: str, baud_rate: int, timeout: float
) -> None:
    """Invalid device configuration fails before any connection attempt."""
    with pytest.raises(ValueError):
        SerialTransportSettings(port, baud_rate=baud_rate, timeout=timeout)
