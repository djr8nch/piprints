# Thermal printer serial transport

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
