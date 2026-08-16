"""Hardware-independent printer contracts and future printer adapters."""

from piprints.printing.base import Printer
from piprints.printing.exceptions import PrintError
from piprints.printing.models import PrintResult

__all__ = ["PrintError", "Printer", "PrintResult"]
