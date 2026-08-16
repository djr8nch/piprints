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

The raw text test initially validated USB byte transport only. Subsequent
staged tests below physically validated the MC206H's acceptance of PiPrints'
ESC/POS `GS v 0` raster command. The command format is documented in Epson's
[GS v 0 command reference](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/gs_lv_0.html).

## Staged raster hardware validation

`scripts/validate_primuz_raster.py` is a manual-only hardware validation tool.
It constructs in-memory `Photo` instances and always submits them through
`create_primuz_usb_printer()`, so its path is:

```text
Photo / PiPrints layout
-> PrimuzThermalPrinter
-> ThermalRasterEncoder
-> UsbPrinterTransport
-> /dev/usb/lp0
```

It neither writes directly to the device nor uses `sudo`. Its documented
development default is `/dev/usb/lp0`; pass `--device` when discovery gives a
different path. It checks that the current user can write to the selected node
before submitting anything.

Run one stage at a time and inspect the paper before explicitly acknowledging a
previous stage:

```bash
.venv/bin/python scripts/validate_primuz_raster.py --stage 1
.venv/bin/python scripts/validate_primuz_raster.py --stage 2 --confirm-stage-1 \
  --printable-width <verified-dot-width>
.venv/bin/python scripts/validate_primuz_raster.py --stage 3 --confirm-stage-1 \
  --confirm-stage-2 --printable-width <verified-dot-width>
```

Stage 1 prints a 64-by-56-dot asymmetric pattern: left-growing black blocks,
a full black bar, a stepped mark at the right edge, offset alternating rows,
and uneven lower blocks. It exposes polarity, horizontal bit order, mirroring,
row order, shifts, and byte-padding errors. Stage 2 prints the provided,
verified printable width with edge markers, a full-width bar, unequal vertical
patterns, alternating blocks, and whitespace. Stage 3 uses
`ClassicPhotoStripLayout` to compose four synthetic photos at that width; it
checks the actual final-layout input shape without requiring a user photo.

## Physical raster validation record

An operator inspected the following outputs on the Raspberry Pi 4 / PRIMUZ
MC206H setup after normal-user device permissions were fixed:

- Stage 1 deterministic raster: passed; black/white polarity, left-to-right
  bit order, row order, and asymmetric right-edge marker were correct;
- Stage 2 full-width raster: passed at 384 dots; both edge markers and the
  continuous horizontal bar printed without clipping, wrapping, mirroring, or
  byte-padding artifacts. The observed output did not leave enough blank paper
  to tear comfortably, so it prompted the narrow printer-adapter correction
  below; and
- the validated 384-dot width is now enforced by
  `create_primuz_usb_printer()` so oversized photos fail before opening the
  device.

`PrimuzThermalPrinter` now appends 32 all-white raster rows (4 mm at 203 dpi)
to each job. This creates tear space using the already validated raster
framing, instead of relying on an unvalidated `ESC d` feed command. A repeated
Stage 2 print confirmed that this margin leaves comfortable tear space while
preserving the correct full-width pattern.

Stage 3 representative layout: passed at 384 dots. The physical output had
four correctly oriented panel rectangles and two dark ovals; the two lighter
grayscale ovals correctly thresholded to white. The full-width strip was
recognizable, was neither mirrored nor clipped, and retained comfortable tear
space. Raster image printing through the validated USB path can now be
considered physically validated for this printer setup.

## Remaining hardware validation

The following remain outside the completed single-job raster validation:

- repeated-job behavior and buffer limits;
- USB disconnect/reconnect recovery;
- paper-out handling; and
- UI responsiveness during a print job.

Do not describe PRIMUZ image printing as physically validated merely because
paper feeds. Record the expected versus observed appearance for all three
stages, including the normal-user device permission result. Repeated jobs,
disconnect recovery, paper-out behavior, and UI responsiveness remain separate
follow-up hardware tests after raster support is validated.
