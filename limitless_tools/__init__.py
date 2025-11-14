from __future__ import annotations

from . import _version as _version  # re-export module for tests/importers

__all__ = ["__version__", "get_version"]

get_version = _version.get_version
__version__ = get_version()
