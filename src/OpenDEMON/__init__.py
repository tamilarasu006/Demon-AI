"""DEMON — modular AI assistant backend with composable intelligence primitives."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from DEMON.sdk import DEMON, DEMONSystem, MemoryHandle, SystemBuilder

try:
    __version__ = _pkg_version("DEMON")
except PackageNotFoundError:  # pragma: no cover — uninstalled source tree
    __version__ = "0.0.0+unknown"

__all__ = ["DEMON", "DEMONSystem", "MemoryHandle", "SystemBuilder", "__version__"]
