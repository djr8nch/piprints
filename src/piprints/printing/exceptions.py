"""Exceptions raised by PiPrints printer implementations."""


class PrintError(RuntimeError):
    """Raised when a printer cannot submit a photo for printing."""


class SerialTransportError(PrintError):
    """Raised when raw bytes cannot be transported over a serial connection."""
