"""Git operations: worktree management, commits, branch ops."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def commit_phase(phase: str, task_id: str, project_root: Path, worktree: Path | None) -> None:
    """Commit all changes after a phase.

    - If worktree exists: commit there (task branch)
    - If architect phase: commit to project_root (main branch)
    - Otherwise: skip
    """
    if worktree and worktree.is_dir():
        commit_dir = worktree
    elif phase == "architect":
        commit_dir = project_root
    else:
        print(f"[git] skipping commit for {phase} (no active worktree)")
        return

    # Stage all changes
    subprocess.run(["git", "add", "-A"], cwd=commit_dir, check=True, capture_output=True)

    # Check if there are staged changes
    result = subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        cwd=commit_dir,
        capture_output=True,
    )

    if result.returncode == 0:
        print(f"[git] nothing to commit for {phase}")
        return

    commit_msg = f"cplus({phase}): {task_id}"
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=commit_dir,
        check=True,
        capture_output=True,
    )
    print(f"[git] committed: {commit_msg}")


def check_already_committed(
    phase: str, task_id: str, project_root: Path, worktree: Path | None = None
) -> None:
    """Warn if a phase commit already exists for this task."""
    commit_msg = f"cplus({phase}): {task_id}"
    check_dir = worktree if (worktree and worktree.is_dir()) else project_root

    result = subprocess.run(
        ["git", "log", "--oneline", f"--grep=^{commit_msg}$"],
        cwd=check_dir,
        capture_output=True,
        text=True,
    )

    if result.stdout.strip():
        print(f"Warning: {phase} phase already committed for {task_id}.", file=sys.stderr)
        print("  Use --from to skip already-done phases, or git reset to redo.", file=sys.stderr)
