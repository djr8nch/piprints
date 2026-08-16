# Thermal printer serial transport and PRIMUZ implementation

PiPrints provides a serial byte-transport boundary for future thermal printer
adapters. The transport is backed by the maintained `pyserial` Python package,
declared in `pyproject.toml` and installed with PiPrints' normal Python
dependencies.

Serial settings are supplied explicitly through `SerialTransportSettings`:

- device path, such as the serial device assigned by Raspberry Pi OS;
- baud rate; and
- optional serial timeout, which defaults to one second.

PiPrints does not select a default device path or baud rate because neither is
hardware-validated for a particular printer model yet. Before configuring a
future printer adapter, identify the device created by Raspberry Pi OS and
confirm the required serial settings from the printer's documentation. The
current transport sends raw bytes only; it does not implement printer commands,
raster framing, or PRIMUZ-specific behavior.

## PRIMUZ MC206H implementation — physical validation pending

`PrimuzThermalPrinter` is present as a pre-hardware-validation adapter for the
PRIMUZ Micro Thermal Printer Ticket Serial Port Printer Module, identified by
retailer listings as MC206H / MC206H_12V. It composes:

```text
PrimuzThermalPrinter
├── ThermalRasterEncoder
└── SerialTransport
    └── PySerialTransport / pyserial
```

The adapter receives the completed PiPrints `Photo`, uses the injected encoder
for monochrome raster data, then sends one framed command through the injected
transport. It does not perform booth layout work, open pyserial directly, or
create a serial connection at application startup. PiPrints remains
digital-only unless an application composition root explicitly injects this
printer.

### Protocol assumption

The PRIMUZ retailer listing says the MC206H provides an ESC/POS instruction
set, but its manufacturer command manual and development kit are not available
in this repository. The adapter therefore makes one explicit, **unverified**
assumption: it frames raster data as ESC/POS `GS v 0` in normal mode:

```text
1D 76 30 00 xL xH yL yH d...
```

`xL/xH` are the encoder's bytes per row and `yL/yH` its height, little-endian.
The byte layout comes from Epson's [GS v 0 command reference](https://download4.epson.biz/sec_pubs/pos/reference_en/escpos/gs_lv_0.html), while the
model listing's [ESC/POS claim](https://www.newegg.com/p/3C6-018V-00CA9) is the
only current PRIMUZ-specific evidence. This is not proof that the MC206H
supports this command, width, raster polarity, or framing.

No initialization, feed, cut, status, density, timing, or baud-rate default
commands are sent. Those details are intentionally deferred until manufacturer
materials and physical validation are available.

### Hardware validation checklist

When the printer arrives, do not treat it as supported until all of the
following are documented and tested:

1. Confirm the exact model, power requirements, interface mode, pinout, and
   safe Raspberry Pi connection or USB-to-serial adapter.
2. Obtain the manufacturer command manual and verify the selected serial port,
   baud rate, parity, flow control, and timeout.
3. Send a minimal diagnostic command from the manufacturer material before
   sending raster data.
4. Validate `GS v 0` support, mode byte, raster dimensions, bit order, black
   polarity, and maximum printable dot width with synthetic patterns.
5. Measure whether explicit initialization, feed, pacing, density, or status
   handling is required; add only behavior confirmed by those results.
6. Validate repeated jobs, paper-out behavior, disconnect recovery, shutdown,
   and UI-thread responsiveness.
