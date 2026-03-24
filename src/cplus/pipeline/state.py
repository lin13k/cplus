"""Task state management (state.md, BLOCKED detection)."""

from __future__ import annotations

import re
from pathlib import Path


def read_worktree_path(state_file: Path) -> str | None:
    """Read worktree path from state.md.

    Looks for lines like: ``- Worktree: `/path/to/worktree```
    Returns None if not found or marked as 'removed'.
    """
    if not state_file.is_file():
        return None

    text = state_file.read_text()
    match = re.search(r"^- Worktree:\s*`([^`]+)`", text, re.MULTILINE)
    if not match:
        return None

    path = match.group(1)
    if path == "removed":
        return None

    return path


def check_blocked(task_dir: Path) -> str | None:
    """Check for BLOCKED file and return reason if found."""
    blocked_file = task_dir / "BLOCKED"
    if blocked_file.is_file():
        return blocked_file.read_text().strip()
    return None
