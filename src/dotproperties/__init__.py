"""Read and write the line-oriented Java Properties format."""

from ._parser import load, loads
from ._writer import dump, dumps

__version__ = "0.2.0"

__all__ = ["__version__", "dump", "dumps", "load", "loads"]
