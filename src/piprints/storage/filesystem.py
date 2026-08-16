"""Filesystem implementation of completed-photo persistence."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

from piprints.imaging import Photo
from piprints.storage.exceptions import PhotoStorageError


class FilesystemPhotoStorage:
    """Save completed photos as uniquely named PNG files below one directory.

    Photos are grouped by their save date. Each filename includes the booth
    session ID and a generated output ID, allowing a session to be saved more
    than once without overwriting an earlier output.
    """

    def __init__(
        self,
        output_directory: Path,
        *,
        date_provider: Callable[[], date] = date.today,
    ) -> None:
        self._output_directory = output_directory
        self._date_provider = date_provider

    def save(self, photo: Photo, *, session_id: UUID) -> Path:
        """Save ``photo`` as a PNG and return its unique filesystem path."""
        output_date = self._date_provider().isoformat()
        destination_directory = self._output_directory / output_date
        destination = destination_directory / f"{session_id}-{uuid4()}.png"
        while destination.exists():
            destination = destination_directory / f"{session_id}-{uuid4()}.png"

        try:
            destination_directory.mkdir(parents=True, exist_ok=True)
            photo.image.save(destination, format="PNG")
        except OSError as error:
            raise PhotoStorageError(
                f"Unable to save photo for session {session_id} to {destination}."
            ) from error

        return destination
