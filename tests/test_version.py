"""Tests for the cplus version command."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from cplus.cli import _handle_version


def test_version_outputs_package_version(capsys):
    """Test that version command outputs the package version from metadata."""
    with patch("importlib.metadata.version", return_value="0.1.0"):
        _handle_version()

    captured = capsys.readouterr()
    assert captured.out == "cplus 0.1.0\n"


def test_version_fallback_when_metadata_unavailable(capsys):
    """Test that version command outputs 'cplus dev' when package metadata is unavailable."""
    from importlib.metadata import PackageNotFoundError

    with patch("importlib.metadata.version", side_effect=PackageNotFoundError("cplus")):
        _handle_version()

    captured = capsys.readouterr()
    assert captured.out == "cplus dev\n"
