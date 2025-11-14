"""Utilities for exposing the installed package version."""

from __future__ import annotations

from importlib import metadata

PACKAGE_NAME = "limitless-tools"
DEFAULT_VERSION = "0.0.0"


def get_version() -> str:
    """Return the installed package version or fallback when unavailable."""
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError:
        return DEFAULT_VERSION
