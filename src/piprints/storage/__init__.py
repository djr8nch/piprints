"""Persistent storage implementations for PiPrints output artifacts."""

from piprints.storage.base import PhotoStorage
from piprints.storage.exceptions import PhotoStorageError, StorageError
from piprints.storage.filesystem import FilesystemPhotoStorage

__all__ = [
    "FilesystemPhotoStorage",
    "PhotoStorage",
    "PhotoStorageError",
    "StorageError",
]
