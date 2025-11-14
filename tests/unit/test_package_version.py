"""Verify package metadata and exposed version helpers."""

from importlib import reload
from unittest.mock import patch

import limitless_tools  # type: ignore


def test_get_version_uses_importlib_metadata() -> None:
    """The internal helper should return the value from importlib.metadata."""
    with patch("limitless_tools._version.metadata.version", return_value="9.9.9"):
        from limitless_tools import _version  # local import to avoid circular deps

        assert _version.get_version() == "9.9.9"


def test_get_version_falls_back_when_metadata_missing() -> None:
    """If the package is not installed, fall back to a sane default version string."""
    from limitless_tools import _version

    error = _version.metadata.PackageNotFoundError("missing")

    with patch("limitless_tools._version.metadata.version", side_effect=error):
        assert _version.get_version() == _version.DEFAULT_VERSION


def test_package_exposes_dunder_version() -> None:
    """Importing the top-level package should set __version__ once."""
    with patch("limitless_tools._version.get_version", return_value="2.0.0"):
        reloaded = reload(limitless_tools)

    assert reloaded.__version__ == "2.0.0"

    # Restore module state for other tests/imports.
    reload(limitless_tools)
