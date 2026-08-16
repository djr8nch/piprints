"""Unit tests for Linux USB printer-class byte transport."""

from __future__ import annotations

import pytest

from piprints.printing import UsbPrinterTransportError
from piprints.printing.thermal import UsbPrinterTransport


class FakeUsbPrinterFile:
    """Record binary device operations without accessing real hardware."""

    def __init__(
        self,
        *,
        write_sizes: list[int] | None = None,
        write_error: Exception | None = None,
        flush_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.write_sizes = write_sizes or []
        self.write_error = write_error
        self.flush_error = flush_error
        self.close_error = close_error
        self.writes: list[bytes] = []
        self.flush_calls = 0
        self.close_calls = 0

    def write(self, data: bytes) -> int:
        """Record one write, optionally simulating partial writes or failure."""
        if self.write_error is not None:
            raise self.write_error
        size = self.write_sizes.pop(0) if self.write_sizes else len(data)
        self.writes.append(bytes(data[:size]))
        return size

    def flush(self) -> None:
        """Record flushing or raise the configured failure."""
        self.flush_calls += 1
        if self.flush_error is not None:
            raise self.flush_error

    def close(self) -> None:
        """Record closing or raise the configured failure."""
        self.close_calls += 1
        if self.close_error is not None:
            raise self.close_error


class RecordingFileFactory:
    """Return an injected device file and capture the requested path and mode."""

    def __init__(self, device_file: FakeUsbPrinterFile) -> None:
        self.device_file = device_file
        self.calls: list[tuple[str, str]] = []

    def __call__(self, path: str, mode: str) -> FakeUsbPrinterFile:
        """Return the fake file without opening a system device."""
        self.calls.append((path, mode))
        return self.device_file


def test_transport_uses_configured_path_writes_exact_bytes_and_closes() -> None:
    """The transport accesses only its injected path and releases the resource."""
    device_file = FakeUsbPrinterFile()
    factory = RecordingFileFactory(device_file)
    transport = UsbPrinterTransport("/dev/usb/lp-test", file_factory=factory)

    transport.open()
    transport.write(b"\x1b\x40PiPrints")
    transport.close()

    assert factory.calls == [("/dev/usb/lp-test", "wb")]
    assert device_file.writes == [b"\x1b\x40PiPrints"]
    assert device_file.flush_calls == 1
    assert device_file.close_calls == 1


def test_transport_preserves_byte_order_across_partial_writes() -> None:
    """Partial low-level writes are completed in original byte order."""
    device_file = FakeUsbPrinterFile(write_sizes=[2, 1])
    transport = UsbPrinterTransport(
        "/dev/usb/lp-test", file_factory=RecordingFileFactory(device_file)
    )

    transport.open()
    transport.write(b"\x10\x20\x30\x40")
    transport.close()

    assert device_file.writes == [b"\x10\x20", b"\x30", b"\x40"]
    assert b"".join(device_file.writes) == b"\x10\x20\x30\x40"
    assert device_file.close_calls == 1


def test_open_failure_includes_device_context() -> None:
    """Opening errors retain both domain type and useful device information."""
    open_error = PermissionError("permission denied")

    def fail_open(path: str, mode: str) -> FakeUsbPrinterFile:
        raise open_error

    transport = UsbPrinterTransport("/dev/usb/lp-test", file_factory=fail_open)

    with pytest.raises(
        UsbPrinterTransportError, match="/dev/usb/lp-test"
    ) as error_info:
        transport.open()

    assert error_info.value.__cause__ is open_error


def test_write_failure_is_translated_and_resource_can_be_closed() -> None:
    """A device failure does not escape the printer transport boundary."""
    write_error = OSError("device disconnected")
    device_file = FakeUsbPrinterFile(write_error=write_error)
    transport = UsbPrinterTransport(
        "/dev/usb/lp-test", file_factory=RecordingFileFactory(device_file)
    )

    transport.open()
    with pytest.raises(UsbPrinterTransportError) as error_info:
        transport.write(b"print data")
    transport.close()

    assert error_info.value.__cause__ is write_error
    assert device_file.close_calls == 1


def test_write_requires_an_open_transport() -> None:
    """Callers receive a domain error instead of an attribute failure."""
    transport = UsbPrinterTransport("/dev/usb/lp-test")

    with pytest.raises(UsbPrinterTransportError, match="must be open"):
        transport.write(b"print data")


@pytest.mark.parametrize("path", ["", None])
def test_transport_rejects_missing_device_path(path: str | None) -> None:
    """Invalid configuration fails before any device open attempt."""
    with pytest.raises(ValueError):
        UsbPrinterTransport(path)  # type: ignore[arg-type]
