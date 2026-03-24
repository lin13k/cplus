"""Tests for pipeline modules."""

from pathlib import Path

from cplus.cli import _parse_args
from cplus.pipeline.checkpoints import parse_checkpoints
from cplus.pipeline.state import check_blocked, read_worktree_path


def test_parse_checkpoints(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("""\
# Implementation Plan

## Checkpoint 1: Setup package

Create pyproject.toml and package structure.

**Files**: pyproject.toml
**Exit Criteria**: pip install works

## Checkpoint 2: Implement CLI

Write the CLI module.

**Files**: src/cli.py

## Summary

All done.
""")
    result = parse_checkpoints(plan)
    assert len(result) == 2
    assert "Setup package" in result[0]
    assert "pyproject.toml" in result[0]
    assert "Implement CLI" in result[1]
    assert "src/cli.py" in result[1]
    # Summary section should NOT be in any checkpoint
    assert all("All done." not in cp for cp in result)


def test_parse_checkpoints_empty(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n\nNo checkpoints here.\n")
    result = parse_checkpoints(plan)
    assert result == []


def test_parse_checkpoints_missing_file(tmp_path: Path) -> None:
    result = parse_checkpoints(tmp_path / "nonexistent.md")
    assert result == []


def test_read_worktree_path(tmp_path: Path) -> None:
    state = tmp_path / "state.md"
    state.write_text("# State\n\n- Phase: SETUP\n- Worktree: `/tmp/my-worktree`\n")
    assert read_worktree_path(state) == "/tmp/my-worktree"


def test_read_worktree_path_removed(tmp_path: Path) -> None:
    state = tmp_path / "state.md"
    state.write_text("# State\n\n- Worktree: `removed`\n")
    assert read_worktree_path(state) is None


def test_read_worktree_path_missing(tmp_path: Path) -> None:
    assert read_worktree_path(tmp_path / "nope.md") is None


def test_read_worktree_path_no_match(tmp_path: Path) -> None:
    state = tmp_path / "state.md"
    state.write_text("# State\n\n- Phase: SETUP\n")
    assert read_worktree_path(state) is None


def test_check_blocked_exists(tmp_path: Path) -> None:
    (tmp_path / "BLOCKED").write_text("Missing dependency X")
    assert check_blocked(tmp_path) == "Missing dependency X"


def test_check_blocked_none(tmp_path: Path) -> None:
    assert check_blocked(tmp_path) is None


# --- CLI arg parsing tests ---

def test_parse_args_empty() -> None:
    parsed = _parse_args([])
    assert parsed["operation"] == "run"
    assert parsed["selector"] is None


def test_parse_args_help() -> None:
    assert _parse_args(["help"])["operation"] == "help"
    assert _parse_args(["--help"])["operation"] == "help"
    assert _parse_args(["-h"])["operation"] == "help"


def test_parse_args_ls_actions() -> None:
    parsed = _parse_args(["ls", "actions"])
    assert parsed["operation"] == "ls"
    assert parsed["sub_args"] == ["actions"]


def test_parse_args_run_with_selector() -> None:
    parsed = _parse_args(["spec"])
    assert parsed["operation"] == "run"
    assert parsed["selector"] == "spec"


def test_parse_args_run_with_roles() -> None:
    parsed = _parse_args(["spec", "--roles", "arch,review"])
    assert parsed["selector"] == "spec"
    assert parsed["roles"] == "arch,review"


def test_parse_args_run_with_extras() -> None:
    parsed = _parse_args(["spec", "extra1", "extra2"])
    assert parsed["selector"] == "spec"
    assert parsed["extras"] == ["extra1", "extra2"]


def test_parse_args_dry_run() -> None:
    parsed = _parse_args(["spec", "--dry-run"])
    assert parsed["dry_run"] is True


def test_parse_args_print_mode() -> None:
    parsed = _parse_args(["spec", "-p"])
    assert parsed["print_mode"] is True


def test_parse_args_develop_v3() -> None:
    parsed = _parse_args(["develop-v3", "spec.md", "--from", "verify"])
    assert parsed["operation"] == "develop-v3"
    assert parsed["sub_args"] == ["spec.md", "--from", "verify"]


def test_parse_args_pick_extras() -> None:
    parsed = _parse_args(["pick", "notes.md", "be strict"])
    assert parsed["operation"] == "pick"
    assert parsed["extras"] == ["notes.md", "be strict"]
