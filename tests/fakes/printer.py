"""A small hardware-independent fake for the PiPrints Printer contract."""

from __future__ import annotations

from collections.abc import Sequence

from piprints.imaging import Photo
from piprints.printing import PrintError, PrintResult


class FakePrinter:
    """Record print submissions and optionally fail every requested print."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self._print_requests: list[Photo] = []

    @property
    def print_requests(self) -> Sequence[Photo]:
        """Return an immutable snapshot of successfully submitted photos."""
        return tuple(self._print_requests)

    @property
    def print_count(self) -> int:
        """Return the number of successfully submitted print requests."""
        return len(self._print_requests)

    def print_photo(self, photo: Photo) -> PrintResult:
        """Record ``photo`` or raise the configured deterministic failure."""
        if self.fail:
            raise PrintError("Fake printer is configured to fail.")
        self._print_requests.append(photo)
        return PrintResult(job_id=f"fake-print-{self.print_count}")
