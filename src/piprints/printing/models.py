"""Value models returned by PiPrints printer implementations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrintResult:
    """The successful submission of one photo to a printer.

    ``job_id`` is optional because some printer backends cannot report an
    identifier for an accepted job. A failure is represented by ``PrintError``
    rather than by a result with a failure flag.
    """

    job_id: str | None = None
