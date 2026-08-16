"""Unit tests for filesystem-backed completed-photo storage."""

from datetime import date
from pathlib import Path
from uuid import UUID

import pytest
from PIL import Image

from piprints.imaging import Photo
from piprints.storage import FilesystemPhotoStorage, PhotoStorageError


def test_storage_creates_dated_directory_and_persists_a_png(tmp_path: Path) -> None:
    """A completed RGB photo is written below the configured output directory."""
    photo = Photo(Image.new("RGB", (11, 7), "red"))
    session_id = UUID("12345678-1234-5678-1234-567812345678")
    storage = FilesystemPhotoStorage(
        tmp_path / "photos", date_provider=lambda: date(2026, 8, 16)
    )

    saved_path = storage.save(photo, session_id=session_id)

    assert saved_path.parent == tmp_path / "photos" / "2026-08-16"
    assert saved_path.exists()
    assert saved_path.suffix == ".png"
    assert str(session_id) in saved_path.stem
    with Image.open(saved_path) as saved_image:
        assert saved_image.mode == "RGB"
        assert saved_image.size == (11, 7)


def test_storage_generates_distinct_names_for_the_same_session(tmp_path: Path) -> None:
    """Repeated saves never overwrite a previously persisted output."""
    photo = Photo(Image.new("RGB", (1, 1), "blue"))
    session_id = UUID("12345678-1234-5678-1234-567812345678")
    storage = FilesystemPhotoStorage(
        tmp_path / "photos", date_provider=lambda: date(2026, 8, 16)
    )

    first_path = storage.save(photo, session_id=session_id)
    second_path = storage.save(photo, session_id=session_id)

    assert first_path != second_path
    assert first_path.exists()
    assert second_path.exists()


def test_storage_translates_an_invalid_output_path(tmp_path: Path) -> None:
    """Filesystem failures are exposed through the storage-domain exception."""
    output_path = tmp_path / "not-a-directory"
    output_path.write_text("not a directory")
    storage = FilesystemPhotoStorage(output_path)

    with pytest.raises(PhotoStorageError, match="Unable to save photo"):
        storage.save(Photo(Image.new("RGB", (1, 1))), session_id=UUID(int=1))
