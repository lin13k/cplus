"""Tests for the cplus status command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from cplus.cli import _handle_status, _parse_args


# --- _parse_args tests ---


def test_parse_args_status_operation():
    """Test that 'status' is recognized as a valid operation."""
    result = _parse_args(["status"])
    assert result["operation"] == "status"


# --- _handle_status tests ---


def test_status_no_project_root(capsys):
    """When no project root is detected, prints 'No active tasks.'"""
    with patch("cplus.cli.find_project_root", return_value=None):
        _handle_status()

    captured = capsys.readouterr()
    assert captured.out == "No active tasks.\n"


def test_status_no_tasks_directory(tmp_path: Path, capsys):
    """When .cplus/tasks/ directory does not exist, prints 'No active tasks.'"""
    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    assert captured.out == "No active tasks.\n"


def test_status_empty_tasks_directory(tmp_path: Path, capsys):
    """When .cplus/tasks/ exists but has no subdirectories, prints 'No active tasks.'"""
    tasks_dir = tmp_path / ".cplus" / "tasks"
    tasks_dir.mkdir(parents=True)

    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    assert captured.out == "No active tasks.\n"


def test_status_single_task_worktree_present(tmp_path: Path, capsys):
    """Single task with an existing worktree shows 'yes' for Exists."""
    tasks_dir = tmp_path / ".cplus" / "tasks"
    task_dir = tasks_dir / "0001-my-task"
    task_dir.mkdir(parents=True)

    worktree_dir = tmp_path / "worktree-0001"
    worktree_dir.mkdir()

    state_md = task_dir / "state.md"
    state_md.write_text(
        "# State: 0001-my-task\n"
        "\n"
        "**Phase**: IMPLEMENT checkpoint-2\n"
        "**Status**: In progress\n"
        "\n"
        "## Environment\n"
        f"- Worktree: `{worktree_dir}`\n"
        "- Branch: `task/0001-my-task`\n"
    )

    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    assert "0001-my-task" in captured.out
    assert "IMPLEMENT checkpoint-2" in captured.out
    assert str(worktree_dir) in captured.out
    assert "Exists:   yes" in captured.out


def test_status_single_task_worktree_missing(tmp_path: Path, capsys):
    """Single task with a non-existent worktree shows 'no' for Exists."""
    tasks_dir = tmp_path / ".cplus" / "tasks"
    task_dir = tasks_dir / "0002-other-task"
    task_dir.mkdir(parents=True)

    missing_worktree = tmp_path / "does-not-exist"

    state_md = task_dir / "state.md"
    state_md.write_text(
        "# State: 0002-other-task\n"
        "\n"
        "**Phase**: VERIFY\n"
        "**Status**: Ready\n"
        "\n"
        "## Environment\n"
        f"- Worktree: `{missing_worktree}`\n"
        "- Branch: `task/0002-other-task`\n"
    )

    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    assert "0002-other-task" in captured.out
    assert "VERIFY" in captured.out
    assert str(missing_worktree) in captured.out
    assert "Exists:   no" in captured.out


def test_status_multiple_tasks(tmp_path: Path, capsys):
    """Multiple tasks are all listed in sorted order."""
    tasks_dir = tmp_path / ".cplus" / "tasks"

    for task_id in ("0003-third", "0001-first", "0002-second"):
        task_dir = tasks_dir / task_id
        task_dir.mkdir(parents=True)
        state_md = task_dir / "state.md"
        state_md.write_text(
            f"# State: {task_id}\n"
            "\n"
            "**Phase**: ARCHITECT complete\n"
            "\n"
            "## Environment\n"
            f"- Worktree: `/tmp/wt-{task_id}`\n"
        )

    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    lines = captured.out

    # All three tasks should appear
    assert "0001-first" in lines
    assert "0002-second" in lines
    assert "0003-third" in lines

    # Sorted order: 0001 before 0002 before 0003
    pos_first = lines.index("0001-first")
    pos_second = lines.index("0002-second")
    pos_third = lines.index("0003-third")
    assert pos_first < pos_second < pos_third


def test_status_malformed_state_md(tmp_path: Path, capsys):
    """Malformed state.md (missing Phase/Worktree) shows 'unknown' defaults."""
    tasks_dir = tmp_path / ".cplus" / "tasks"
    task_dir = tasks_dir / "0004-broken"
    task_dir.mkdir(parents=True)

    state_md = task_dir / "state.md"
    state_md.write_text("This is not a valid state file.\nNo structured fields here.\n")

    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    assert "0004-broken" in captured.out
    assert "Phase:    unknown" in captured.out
    assert "Worktree: unknown" in captured.out
    assert "Exists:   no" in captured.out


def test_status_no_state_md_file(tmp_path: Path, capsys):
    """Task directory exists but has no state.md — shows 'unknown' defaults."""
    tasks_dir = tmp_path / ".cplus" / "tasks"
    task_dir = tasks_dir / "0005-no-state"
    task_dir.mkdir(parents=True)

    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    assert "0005-no-state" in captured.out
    assert "Phase:    unknown" in captured.out
    assert "Worktree: unknown" in captured.out
    assert "Exists:   no" in captured.out


def test_status_exit_code_always_zero():
    """Status command always returns (no sys.exit), so exit code is 0."""
    with patch("cplus.cli.find_project_root", return_value=None):
        # Should not raise SystemExit
        _handle_status()


def test_status_files_in_tasks_dir_ignored(tmp_path: Path, capsys):
    """Files (not directories) in .cplus/tasks/ are ignored."""
    tasks_dir = tmp_path / ".cplus" / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "README.md").write_text("This is not a task.")

    with patch("cplus.cli.find_project_root", return_value=tmp_path):
        _handle_status()

    captured = capsys.readouterr()
    assert captured.out == "No active tasks.\n"
