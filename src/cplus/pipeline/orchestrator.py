"""Phase sequencing, --from resume, error handling for develop-v3."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from cplus.pipeline.checkpoints import parse_checkpoints
from cplus.pipeline.git import check_already_committed, commit_phase
from cplus.pipeline.phase import run_phase
from cplus.pipeline.state import read_worktree_path


PHASE_ORDER = ["architect", "setup", "implement", "verify", "review", "cleanup"]

# Phases that require the most capable model for best results.
# Uses Claude CLI aliases (e.g. "opus") which auto-resolve to the latest version.
HEAVY_PHASES = {"architect", "review"}


@dataclass
class PipelineConfig:
    spec_file: Path
    from_phase: str | None
    from_checkpoint: int
    task_id: str
    task_dir: Path
    project_root: Path
    roles_dir: Path
    model: str | None = None


def _model_for_phase(phase: str, user_model: str | None) -> str | None:
    """Return the model for a phase: user override wins, else 'opus' for heavy phases."""
    if user_model:
        return user_model
    if phase in HEAVY_PHASES:
        return "opus"
    return None


def run_pipeline(config: PipelineConfig) -> None:
    """Execute the develop-v3 pipeline."""
    print(f"develop-v3: {config.task_id}")
    if config.from_phase:
        if config.from_checkpoint > 0:
            print(f"Resuming from: checkpoint-{config.from_checkpoint}")
        else:
            print(f"Resuming from: {config.from_phase}")

    # Determine start index
    start_idx = 0
    if config.from_phase:
        try:
            start_idx = PHASE_ORDER.index(config.from_phase)
        except ValueError:
            print(f"Error: invalid phase '{config.from_phase}'", file=sys.stderr)
            sys.exit(1)

    # Pre-load worktree path when resuming past setup
    worktree_path: str | None = None
    if config.from_phase and config.from_phase not in ("architect", "setup"):
        state_file = config.task_dir / "state.md"
        worktree_path = read_worktree_path(state_file)

    for idx, phase in enumerate(PHASE_ORDER):
        if idx < start_idx:
            continue

        worktree = Path(worktree_path) if worktree_path else None

        if phase == "architect":
            check_already_committed("architect", config.task_id, config.project_root)
            run_phase(
                "architect",
                config.roles_dir / "architect.md",
                config.task_dir,
                [config.spec_file, config.task_dir],
                model=_model_for_phase("architect", config.model),
            )
            commit_phase("architect", config.task_id, config.project_root, None)

        elif phase == "setup":
            check_already_committed("setup", config.task_id, config.project_root)
            run_phase(
                "setup",
                config.roles_dir / "setup.md",
                config.task_dir,
                [config.task_dir / "plan.md", config.task_dir / "state.md"],
                model=_model_for_phase("setup", config.model),
            )
            state_file = config.task_dir / "state.md"
            worktree_path = read_worktree_path(state_file)
            worktree = Path(worktree_path) if worktree_path else None
            commit_phase("setup", config.task_id, config.project_root, worktree)

        elif phase == "implement":
            plan_file = config.task_dir / "plan.md"
            if not plan_file.is_file():
                print("Error: plan.md not found -- did architect phase run?", file=sys.stderr)
                sys.exit(1)

            checkpoints = parse_checkpoints(plan_file)
            if not checkpoints:
                print("Warning: no checkpoints found in plan.md -- skipping implement phase")
                continue

            for cp_idx, cp_content in enumerate(checkpoints, 1):
                if cp_idx < config.from_checkpoint:
                    print(f"[checkpoint-{cp_idx}] skipped (--from checkpoint-{config.from_checkpoint})")
                    continue

                # Write checkpoint content to temp file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".md", delete=False, prefix="checkpoint-"
                ) as tmp:
                    tmp.write(cp_content)
                    tmp_path = Path(tmp.name)

                try:
                    run_phase(
                        f"checkpoint-{cp_idx}",
                        config.roles_dir / "implement.md",
                        config.task_dir,
                        [config.task_dir / "task.md", config.task_dir / "state.md", tmp_path],
                        model=_model_for_phase("implement", config.model),
                        cwd=worktree,
                    )
                finally:
                    tmp_path.unlink(missing_ok=True)

                commit_phase(f"checkpoint-{cp_idx}", config.task_id, config.project_root, worktree)

        elif phase == "verify":
            check_already_committed("verify", config.task_id, config.project_root, worktree)
            run_phase(
                "verify",
                config.roles_dir / "verify.md",
                config.task_dir,
                [config.task_dir / "task.md", config.task_dir / "state.md", config.task_dir / "plan.md"],
                model=_model_for_phase("verify", config.model),
                cwd=worktree,
            )
            commit_phase("verify", config.task_id, config.project_root, worktree)

        elif phase == "review":
            check_already_committed("review", config.task_id, config.project_root, worktree)
            run_phase(
                "review",
                config.roles_dir / "review.md",
                config.task_dir,
                [config.task_dir / "task.md", config.task_dir / "plan.md", config.task_dir / "report.md"],
                model=_model_for_phase("review", config.model),
                cwd=worktree,
            )
            commit_phase("review", config.task_id, config.project_root, worktree)

        elif phase == "cleanup":
            check_already_committed("cleanup", config.task_id, config.project_root, worktree)
            run_phase(
                "cleanup",
                config.roles_dir / "cleanup.md",
                config.task_dir,
                [config.task_dir / "state.md"],
                model=_model_for_phase("cleanup", config.model),
                cwd=config.project_root,
            )
            # Commit to project_root since cleanup removes the worktree
            commit_phase("cleanup", config.task_id, config.project_root, None)

    print(f"\ndevelop-v3 complete: {config.task_id}")


def run_develop_v3_cli(args: list[str], prompts_dir: Path) -> None:
    """Parse develop-v3 CLI args and run the pipeline."""

    spec_file: str | None = None
    from_phase: str | None = None
    from_checkpoint = 0
    model: str | None = None

    argv = list(args)
    while argv:
        arg = argv[0]
        if arg == "--from":
            argv.pop(0)
            if not argv:
                print("Error: --from requires a phase name", file=sys.stderr)
                print(
                    "Valid values: architect, setup, implement, checkpoint-N, verify, review, cleanup",
                    file=sys.stderr,
                )
                sys.exit(1)
            from_phase = argv.pop(0)
        elif arg.startswith("--from="):
            from_phase = arg[len("--from="):]
            argv.pop(0)
        elif arg == "--model":
            argv.pop(0)
            if not argv:
                print("Error: --model requires a value", file=sys.stderr)
                sys.exit(1)
            model = argv.pop(0)
        elif arg.startswith("--model="):
            model = arg[len("--model="):]
            argv.pop(0)
        elif arg.startswith("-"):
            print(f"Error: Unknown option {arg}", file=sys.stderr)
            sys.exit(1)
        else:
            if spec_file is None:
                spec_file = arg
            argv.pop(0)

    if spec_file is None:
        print("Error: spec file required", file=sys.stderr)
        print("Usage: cplus develop-v3 <spec-file> [--from <phase>]", file=sys.stderr)
        sys.exit(1)

    spec_path = Path(spec_file)
    if not spec_path.is_file():
        print(f"Error: spec file not found: {spec_file}", file=sys.stderr)
        sys.exit(1)

    # Validate --from value
    if from_phase:
        checkpoint_match = re.match(r"^checkpoint-(\d+)$", from_phase)
        if checkpoint_match:
            from_checkpoint = int(checkpoint_match.group(1))
            from_phase = "implement"
        elif from_phase not in PHASE_ORDER:
            print(f"Error: invalid --from value: {from_phase}", file=sys.stderr)
            print(
                "Valid values: architect, setup, implement, checkpoint-N, verify, review, cleanup",
                file=sys.stderr,
            )
            sys.exit(1)

    # Derive task_id from spec filename
    task_id = spec_path.stem

    # Project root and task dir
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    project_root = Path(result.stdout.strip()) if result.returncode == 0 else Path.cwd()
    task_dir = project_root / ".cplus" / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    roles_dir = prompts_dir / "roles" / "develop-v3"

    config = PipelineConfig(
        spec_file=spec_path,
        from_phase=from_phase,
        from_checkpoint=from_checkpoint,
        task_id=task_id,
        task_dir=task_dir,
        project_root=project_root,
        roles_dir=roles_dir,
        model=model,
    )

    run_pipeline(config)
