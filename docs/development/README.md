# Development

- [Setup](setup.md)
- [Testing](testing.md)

PiPrints is developed and run primarily on Raspberry Pi OS. The setup guide
explains the supported environment; the testing guide describes the
hardware-independent CI boundaries.

The current UI identity is centralized in `piprints.ui.styling`. New screens
should use its semantic button/status helpers and shared tokens rather than
adding independent QSS or raw color values. The present pink and mint palette
is the default PiPrints style; full theme customization remains future work.
