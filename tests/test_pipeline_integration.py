"""Integration tests for the develop-v3 pipeline orchestrator.

These tests stub out `run_phase` and `commit_phase` (the subprocess boundaries)
to verify that the orchestrator passes the correct context files to each phase,
sequences phases properly, and handles resume/blocked scenarios.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from cplus.pipeline.orchestrator import PipelineConfig, run_pipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def pipeline_env(tmp_path: Path) -> dict:
    """Set up a minimal filesystem for a full pipeline run.

    Returns a dict with all paths and a ready-to-use PipelineConfig.
    """
    project_root = tmp_path / "project"
    project_root.mkdir()

    task_id = "0001-test-feature"
    task_dir = project_root / ".cplus" / "tasks" / task_id
    task_dir.mkdir(parents=True)

    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    for role in ("architect", "setup", "implement", "verify", "review", "cleanup"):
        (roles_dir / f"{role}.md").write_text(f"# {role} role stub")

    spec_file = tmp_path / "spec.md"
    spec_file.write_text("# Spec\n\nDo the thing.\n")

    # plan.md with two checkpoints (created by architect in real runs)
    plan_md = task_dir / "plan.md"
    plan_md.write_text(
        "# Plan\n\n"
        "## Checkpoint 1: Setup basics\n\n"
        "**Description**: Create the skeleton\n"
        "**Files**: src/main.py\n"
        "**Test command**: python -m pytest\n"
        "**Acceptance criteria**:\n- Skeleton exists\n"
        "**Dependencies**: None\n\n"
        "## Checkpoint 2: Add feature\n\n"
        "**Description**: Implement the feature\n"
        "**Files**: src/feature.py\n"
        "**Test command**: python -m pytest\n"
        "**Acceptance criteria**:\n- Feature works\n"
        "**Dependencies**: Checkpoint 1\n"
    )

    # task.md (created by architect)
    (task_dir / "task.md").write_text("# Task: Test Feature\n\n## Goal\nTest.\n")

    # state.md with worktree path (created by architect, updated by setup)
    worktree_path = tmp_path / "project-0001-test-feature"
    worktree_path.mkdir()
    (task_dir / "state.md").write_text(
        "# State: 0001-test-feature\n\n"
        f"## Environment\n- Worktree: `{worktree_path}`\n"
        "- Branch: `task/0001-test-feature`\n"
    )

    # report.md (created by verify)
    (task_dir / "report.md").write_text("# Report\n\n**Verdict**: PASS\n")

    config = PipelineConfig(
        spec_file=spec_file,
        from_phase=None,
        from_checkpoint=0,
        task_id=task_id,
        task_dir=task_dir,
        project_root=project_root,
        roles_dir=roles_dir,
    )

    return {
        "config": config,
        "task_dir": task_dir,
        "project_root": project_root,
        "worktree_path": worktree_path,
        "spec_file": spec_file,
        "roles_dir": roles_dir,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PATCH_BASE = "cplus.pipeline.orchestrator"


def _stub_run_phase_with_setup(env: dict):
    """Return a run_phase side_effect that simulates setup writing worktree to state.md."""
    worktree_path = env["worktree_path"]
    task_dir = env["task_dir"]

    def side_effect(name, role_file, task_dir_, context_files, *, model=None, cwd=None):
        # Simulate setup phase writing the Environment section
        if name == "setup":
            state = task_dir / "state.md"
            state.write_text(
                "# State\n\n"
                f"## Environment\n- Worktree: `{worktree_path}`\n"
                "- Branch: `task/0001-test-feature`\n"
            )

    return side_effect


# ---------------------------------------------------------------------------
# Tests: Context file handover per phase
# ---------------------------------------------------------------------------

@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_architect_receives_spec_and_task_dir(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """ARCHITECT should receive the spec file and task directory."""
    config = pipeline_env["config"]
    config.from_phase = "architect"
    # Only run architect by patching PHASE_ORDER to just architect
    mock_run_phase.side_effect = _stub_run_phase_with_setup(pipeline_env)

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["architect"]):
        run_pipeline(config)

    mock_run_phase.assert_called_once()
    _, _, _, context_files = mock_run_phase.call_args[0]
    assert context_files == [config.spec_file, config.task_dir]


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_setup_receives_plan_and_state(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """SETUP should receive plan.md and state.md."""
    config = pipeline_env["config"]
    config.from_phase = "setup"
    mock_run_phase.side_effect = _stub_run_phase_with_setup(pipeline_env)
    task_dir = pipeline_env["task_dir"]

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["setup"]):
        run_pipeline(config)

    mock_run_phase.assert_called_once()
    _, _, _, context_files = mock_run_phase.call_args[0]
    assert context_files == [task_dir / "plan.md", task_dir / "state.md"]


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_implement_receives_task_state_and_checkpoint(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """IMPLEMENT should receive task.md, state.md, and the checkpoint temp file."""
    config = pipeline_env["config"]
    config.from_phase = "implement"
    task_dir = pipeline_env["task_dir"]

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["implement"]):
        run_pipeline(config)

    # Two checkpoints → two run_phase calls
    assert mock_run_phase.call_count == 2

    for call_args in mock_run_phase.call_args_list:
        _, _, _, context_files = call_args[0]
        assert len(context_files) == 3
        assert context_files[0] == task_dir / "task.md"
        assert context_files[1] == task_dir / "state.md"
        # Third arg is a temp file path — just verify it's a Path
        assert isinstance(context_files[2], Path)


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_verify_receives_task_state_and_plan(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """VERIFY should receive task.md, state.md, and plan.md."""
    config = pipeline_env["config"]
    config.from_phase = "verify"
    task_dir = pipeline_env["task_dir"]

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["verify"]):
        run_pipeline(config)

    mock_run_phase.assert_called_once()
    _, _, _, context_files = mock_run_phase.call_args[0]
    assert context_files == [
        task_dir / "task.md",
        task_dir / "state.md",
        task_dir / "plan.md",
    ]


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_review_receives_task_plan_and_report(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """REVIEW should receive task.md, plan.md, and report.md."""
    config = pipeline_env["config"]
    config.from_phase = "review"
    task_dir = pipeline_env["task_dir"]

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["review"]):
        run_pipeline(config)

    mock_run_phase.assert_called_once()
    _, _, _, context_files = mock_run_phase.call_args[0]
    assert context_files == [
        task_dir / "task.md",
        task_dir / "plan.md",
        task_dir / "report.md",
    ]


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_cleanup_receives_state(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """CLEANUP should receive state.md and run from project root."""
    config = pipeline_env["config"]
    config.from_phase = "cleanup"
    task_dir = pipeline_env["task_dir"]

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["cleanup"]):
        run_pipeline(config)

    mock_run_phase.assert_called_once()
    _, _, _, context_files = mock_run_phase.call_args[0]
    assert context_files == [task_dir / "state.md"]
    assert mock_run_phase.call_args[1]["cwd"] == config.project_root


# ---------------------------------------------------------------------------
# Tests: Cleanup commits to project root (not worktree)
# ---------------------------------------------------------------------------

@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_cleanup_commits_to_project_root_not_worktree(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """CLEANUP should commit with worktree=None since the worktree is removed."""
    config = pipeline_env["config"]
    config.from_phase = "cleanup"

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["cleanup"]):
        run_pipeline(config)

    mock_commit.assert_called_once_with(
        "cleanup", config.task_id, config.project_root, None
    )


# ---------------------------------------------------------------------------
# Tests: Phase sequencing and --from resume
# ---------------------------------------------------------------------------

@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_full_pipeline_phase_order(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """Full pipeline should run all phases in order."""
    config = pipeline_env["config"]
    mock_run_phase.side_effect = _stub_run_phase_with_setup(pipeline_env)

    run_pipeline(config)

    phase_names = [c[0][0] for c in mock_run_phase.call_args_list]
    assert phase_names == [
        "architect",
        "setup",
        "checkpoint-1",
        "checkpoint-2",
        "verify",
        "review",
        "cleanup",
    ]


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_from_verify_skips_earlier_phases(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """--from verify should skip architect, setup, and implement."""
    config = pipeline_env["config"]
    config.from_phase = "verify"

    run_pipeline(config)

    phase_names = [c[0][0] for c in mock_run_phase.call_args_list]
    assert phase_names == ["verify", "review", "cleanup"]


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_from_checkpoint_2_skips_checkpoint_1(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """--from checkpoint-2 should skip checkpoint-1 but run checkpoint-2 onward."""
    config = pipeline_env["config"]
    config.from_phase = "implement"
    config.from_checkpoint = 2

    run_pipeline(config)

    phase_names = [c[0][0] for c in mock_run_phase.call_args_list]
    assert phase_names == ["checkpoint-2", "verify", "review", "cleanup"]


# ---------------------------------------------------------------------------
# Tests: BLOCKED file detection
# ---------------------------------------------------------------------------

@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_blocked_file_halts_pipeline(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """If a phase writes a BLOCKED file, run_phase should detect it and exit.

    Note: BLOCKED detection is in run_phase (which we stub here), so this test
    verifies the orchestrator's contract — run_phase raises SystemExit on BLOCKED.
    """
    task_dir = pipeline_env["task_dir"]
    config = pipeline_env["config"]
    config.from_phase = "verify"

    def write_blocked(name, *args, **kwargs):
        if name == "verify":
            (task_dir / "BLOCKED").write_text("BLOCKED: tests cannot run")
            raise SystemExit(1)

    mock_run_phase.side_effect = write_blocked

    with pytest.raises(SystemExit):
        run_pipeline(config)

    # Review and cleanup should NOT have run
    phase_names = [c[0][0] for c in mock_run_phase.call_args_list]
    assert phase_names == ["verify"]


# ---------------------------------------------------------------------------
# Tests: Model selection
# ---------------------------------------------------------------------------

@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_heavy_phases_use_opus_by_default(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """Architect and review should default to 'opus' model."""
    config = pipeline_env["config"]
    mock_run_phase.side_effect = _stub_run_phase_with_setup(pipeline_env)

    run_pipeline(config)

    models_by_phase = {
        c[0][0]: c[1].get("model") for c in mock_run_phase.call_args_list
    }
    assert models_by_phase["architect"] == "opus"
    assert models_by_phase["review"] == "opus"
    assert models_by_phase["setup"] is None
    assert models_by_phase["verify"] is None


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_user_model_overrides_default(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """--model flag should override the default model for all phases."""
    config = pipeline_env["config"]
    config.model = "sonnet"
    mock_run_phase.side_effect = _stub_run_phase_with_setup(pipeline_env)

    run_pipeline(config)

    for call_args in mock_run_phase.call_args_list:
        assert call_args[1].get("model") == "sonnet"


# ---------------------------------------------------------------------------
# Tests: Implement phase runs in worktree
# ---------------------------------------------------------------------------

@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_implement_runs_in_worktree(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """IMPLEMENT checkpoints should run with cwd set to the worktree."""
    config = pipeline_env["config"]
    config.from_phase = "implement"
    worktree = pipeline_env["worktree_path"]

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["implement"]):
        run_pipeline(config)

    for call_args in mock_run_phase.call_args_list:
        assert call_args[1]["cwd"] == worktree


@patch(f"{PATCH_BASE}.commit_phase")
@patch(f"{PATCH_BASE}.check_already_committed")
@patch(f"{PATCH_BASE}.run_phase")
def test_verify_and_review_run_in_worktree(
    mock_run_phase: MagicMock,
    mock_check: MagicMock,
    mock_commit: MagicMock,
    pipeline_env: dict,
) -> None:
    """VERIFY and REVIEW should run with cwd set to the worktree."""
    config = pipeline_env["config"]
    config.from_phase = "verify"
    worktree = pipeline_env["worktree_path"]

    with patch(f"{PATCH_BASE}.PHASE_ORDER", ["verify", "review"]):
        run_pipeline(config)

    assert mock_run_phase.call_count == 2
    for call_args in mock_run_phase.call_args_list:
        assert call_args[1]["cwd"] == worktree
