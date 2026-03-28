"""Single phase execution (subprocess to claude -p)."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


def run_phase(
    name: str,
    role_file: Path,
    task_dir: Path,
    context_files: list[Path],
    *,
    model: str | None = None,
    cwd: Path | None = None,
) -> None:
    """Run a single pipeline phase via `cplus -p --dangerously-skip-permissions`.

    Args:
        name: Phase name (e.g., "architect", "checkpoint-1")
        role_file: Path to the role .md file
        task_dir: Task workspace directory
        context_files: Additional context files to pass
        model: Optional model override to pass via --model
        cwd: Working directory for the subprocess (e.g., worktree path)
    """
    print(f"\n[{name}] starting...")

    # Remove stale BLOCKED file from previous run
    blocked_file = task_dir / "BLOCKED"
    blocked_file.unlink(missing_ok=True)

    if not role_file.is_file():
        print(f"Error: role file not found: {role_file}", file=sys.stderr)
        sys.exit(1)

    # Build cplus command: cplus -p --dangerously-skip-permissions <role> <context_files>
    cmd = ["cplus", "-p", "--dangerously-skip-permissions"]
    if model:
        cmd.extend(["--model", model])
    cmd.append(str(role_file))
    for cf in context_files:
        cmd.append(str(cf))

    if cwd:
        print(f"[{name}] cwd: {cwd}")

    start = time.time()
    result = subprocess.run(cmd, cwd=cwd)
    elapsed = int(time.time() - start)

    # Check for BLOCKED file
    if blocked_file.is_file():
        reason = blocked_file.read_text().strip()
        print(f"\n[BLOCKED] {reason}", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        print(f"\n[{name}] FAILED (exit code {result.returncode})", file=sys.stderr)
        sys.exit(1)

    print(f"[{name}] done ({elapsed}s)")
