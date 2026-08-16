"""Exceptions raised by PiPrints storage components."""


class StorageError(RuntimeError):
    """Base class for errors raised while persisting PiPrints data."""


class PhotoStorageError(StorageError):
    """Raised when a completed photo cannot be saved."""
