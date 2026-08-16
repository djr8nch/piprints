"""Exceptions raised by PiPrints printer implementations."""


class PrintError(RuntimeError):
    """Raised when a printer cannot submit a photo for printing."""


class PrinterTransportError(PrintError):
    """Raised when a printer byte transport cannot complete an operation."""


class SerialTransportError(PrinterTransportError):
    """Raised when raw bytes cannot be transported over a serial connection."""


class UsbPrinterTransportError(PrinterTransportError):
    """Raised when raw bytes cannot be transported to a USB printer device."""
