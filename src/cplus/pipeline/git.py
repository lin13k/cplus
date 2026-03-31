"""Git operations: worktree management, commits, branch ops."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def setup_worktree(task_id: str, install_cmd: str | None = None) -> None:
    """Create a git worktree for a develop-v3 task.

    Creates worktree at ../<project>-<task-id> on branch task/<task-id>.
    Optionally runs an install command. Updates state.md with environment info.
    """
    project_root = _get_project_root()
    project_name = project_root.name
    worktree_path = project_root.parent / f"{project_name}-{task_id}"
    branch = f"task/{task_id}"
    task_dir = project_root / ".cplus" / "tasks" / task_id
    state_file = task_dir / "state.md"

    # Create worktree + branch
    if worktree_path.is_dir():
        print(f"Worktree already exists: {worktree_path}")
        result = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True,
        )
        current_branch = result.stdout.strip()
        if current_branch != branch:
            print(f"Error: worktree exists but is on branch '{current_branch}', expected '{branch}'", file=sys.stderr)
            sys.exit(1)
        print(f"Reusing existing worktree (branch: {branch})")
    else:
        print(f"Creating worktree: {worktree_path} (branch: {branch})")
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch],
            cwd=project_root, check=True,
        )

    # Install dependencies
    install_status = "skipped"
    if install_cmd:
        print(f"Installing dependencies: {install_cmd}")
        result = subprocess.run(install_cmd, shell=True, cwd=worktree_path)
        if result.returncode != 0:
            print("Error: install command failed", file=sys.stderr)
            sys.exit(1)
        install_status = "verified"
    else:
        print("No install command provided, skipping dependency installation")

    # Verify clean state
    result = subprocess.run(
        ["git", "-C", str(worktree_path), "status", "--porcelain"],
        capture_output=True, text=True,
    )
    if result.stdout.strip():
        print("Warning: worktree has uncommitted changes after install")

    # Update state.md
    task_dir.mkdir(parents=True, exist_ok=True)
    _append_environment_to_state(state_file, str(worktree_path), branch, install_status)

    print(f"\nSetup complete:")
    print(f"  Worktree: {worktree_path}")
    print(f"  Branch:   {branch}")
    print(f"  Install:  {install_status}")


def cleanup_worktree(task_id: str) -> None:
    """Remove the git worktree for a develop-v3 task.

    Removes worktree, prunes references. Does NOT delete the task branch.
    Updates state.md.
    """
    project_root = _get_project_root()
    project_name = project_root.name
    worktree_path = project_root.parent / f"{project_name}-{task_id}"
    task_dir = project_root / ".cplus" / "tasks" / task_id
    state_file = task_dir / "state.md"

    # Remove worktree
    if worktree_path.is_dir():
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "-C", str(worktree_path), "status", "--porcelain"],
            capture_output=True, text=True,
        )
        if result.stdout.strip():
            print("Error: worktree has uncommitted changes:", file=sys.stderr)
            subprocess.run(["git", "-C", str(worktree_path), "status", "--short"], file=sys.stderr)
            print("\nCommit or discard changes before cleanup.", file=sys.stderr)
            sys.exit(1)

        print(f"Removing worktree: {worktree_path}")
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path)],
            cwd=project_root, check=True,
        )
    else:
        print(f"Worktree already removed: {worktree_path}")

    # Prune stale references
    subprocess.run(["git", "worktree", "prune"], cwd=project_root, check=True)
    print("Pruned stale worktree references")

    # Update state.md
    if state_file.is_file():
        _append_cleanup_to_state(state_file, task_id)

    print(f"\nCleanup complete:")
    print(f"  Worktree: removed")
    print(f"  Branch:   task/{task_id} (kept)")


def _get_project_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("Error: not in a git repository", file=sys.stderr)
        sys.exit(1)
    return Path(result.stdout.strip())


def _append_environment_to_state(
    state_file: Path, worktree_path: str, branch: str, install_status: str,
) -> None:
    """Append or replace the Environment section in state.md."""
    text = state_file.read_text() if state_file.is_file() else ""
    text = _remove_environment_section(text)
    text += (
        f"\n## Environment\n"
        f"- Worktree: `{worktree_path}`\n"
        f"- Branch: `{branch}`\n"
        f"- Install: {install_status}\n"
    )
    state_file.write_text(text)


def _append_cleanup_to_state(state_file: Path, task_id: str) -> None:
    """Append cleanup status to state.md."""
    text = state_file.read_text()
    text = _remove_environment_section(text)
    text += (
        f"\n**Phase**: CLEANUP complete\n"
        f"**Status**: Done\n"
        f"\n## Environment\n"
        f"- Worktree: removed\n"
        f"- Branch: `task/{task_id}` (kept for reference)\n"
    )
    state_file.write_text(text)


def _remove_environment_section(text: str) -> str:
    """Remove existing ## Environment section from state.md text."""
    import re
    # Remove from "## Environment" to next "## " heading or end of file
    return re.sub(r"\n## Environment\n.*?(?=\n## |\Z)", "", text, flags=re.DOTALL)


def merge_task_branch(branch: str, project_root: Path) -> None:
    """Merge a task branch into the current branch.

    Exits with code 1 and writes BLOCKED if merge conflicts occur.
    """
    print(f"[git] merging {branch} into current branch")
    result = subprocess.run(
        ["git", "merge", branch, "-m", f"Merge {branch}"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Abort the failed merge to leave a clean state
        subprocess.run(
            ["git", "merge", "--abort"],
            cwd=project_root,
            capture_output=True,
        )
        print(f"Error: merge conflict merging {branch}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    print(f"[git] merged: {branch}")


def rewrite_environment_section(
    state_file: Path, worktree_path: str, branch: str,
) -> None:
    """Re-append the Environment section to state.md (e.g. after architect overwrites it)."""
    _append_environment_to_state(state_file, worktree_path, branch, "verified")


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
