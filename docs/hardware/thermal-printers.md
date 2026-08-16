# Thermal printer transport and PRIMUZ MC206H

PiPrints separates printer protocol from the byte transport that reaches a
device. `PrimuzThermalPrinter` owns ESC/POS raster framing, while an injected
`PrinterTransport` owns the connection lifecycle and raw byte delivery:

```text
PrimuzThermalPrinter
├── ThermalRasterEncoder
└── PrinterTransport
    ├── PySerialTransport
    └── UsbPrinterTransport
```

The transport contract is deliberately small: `open()`, `write(data: bytes)`,
and `close()`. A transport sends already-framed bytes only; it does not know
about ESC/POS commands, raster encoding, feeds, printer policy, booth state,
or UI behavior. `SerialTransport` remains the serial-specific protocol name
for compatibility, and `PySerialTransport` continues to use `pyserial` with
explicit `SerialTransportSettings` (port, baud rate, optional timeout).

## Validated USB hardware

The following physical result is the current source of truth for PiPrints:

- printer: PRIMUZ MC206H;
- host: Raspberry Pi 4;
- USB vendor ID: `0485`;
- USB product ID: `5741`;
- USB product string: `Virtual PRN`;
- Linux driver: `usblp`;
- observed character device: `/dev/usb/lp0`; and
- raw ESC/POS text communication succeeded.

The successful diagnostic command was:

```bash
printf '\x1b\x40PiPrints USB test\n\n\n' | sudo tee /dev/usb/lp0 > /dev/null
```

The printer is therefore a Linux USB printer-class device in this validated
setup, not a `/dev/ttyUSB*` or `/dev/ttyACM*` serial device. USB through
`usblp` is the currently validated and recommended PiPrints transport for this
hardware. Device paths can vary between systems; PiPrints does not assume that
every installation will use `/dev/usb/lp0`.

## USB transport

`UsbPrinterTransport(device_path, *, file_factory=...)` writes to a configured
Linux printer-class character device such as `/dev/usb/lp0`, using normal
binary file I/O. It opens the device for each print operation, writes every
provided byte (including retrying partial writes), flushes, and closes it. The
per-operation lifecycle matches the PRIMUZ adapter and avoids holding a stale
file handle if a USB cable is disconnected between jobs. Errors identify the
configured device path and preserve their low-level cause as
`UsbPrinterTransportError`.

The optional `file_factory` is a test seam; production uses Python's built-in
binary `open`. No `pyusb` or `libusb` dependency is needed because Linux
already exposes the working device node.

## PRIMUZ raster protocol status

`PrimuzThermalPrinter` receives a completed PiPrints `Photo`, encodes it with
the injected `ThermalRasterEncoder`, and sends one ESC/POS `GS v 0` raster
command through any `PrinterTransport`. It has no branch for USB or serial;
bootstrap or future explicit printer configuration selects the transport.

The raw text test validates USB byte transport only. It does **not** yet prove
that the MC206H accepts PiPrints' raster command, raster dimensions, polarity,
or bit order. The adapter's raster command remains an ESC/POS assumption based
on Epson's [GS v 0 command reference](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/gs_lv_0.html).

## Next hardware validation

Wire `UsbPrinterTransport("/dev/usb/lp0")` into `PrimuzThermalPrinter` at the
composition boundary, then print a small representative PiPrints raster image.
Confirm visible output, dot polarity, bit order, dimensions, and required feed
behavior before marking image-printing hardware validation complete. Also test
repeated jobs, disconnect recovery, paper-out behavior, and UI responsiveness.
