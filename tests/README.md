# PiPrints tests

## Unit

Fast, deterministic, hardware-independent tests of individual package, camera
adapter, and booth-domain behavior. These tests must not require a Raspberry Pi
camera or a Qt display stack.

## Integration

Tests that cross subsystem boundaries, including PySide6 widgets, application
bootstrap, and main-window composition. They use `QT_QPA_PLATFORM=offscreen`
for headless execution.

## Hardware

Reserved for future Raspberry Pi-specific automated validation. Current camera
hardware checks remain manual scripts and documented procedures. Default CI
must never require Raspberry Pi hardware.
