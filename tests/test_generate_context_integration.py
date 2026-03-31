"""Integration tests for: cplus generate-context

Stubs out subprocess.run (the Claude CLI boundary) and verifies that
_handle_generate_context composes the correct prompt, sequences flags,
and handles error paths.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cplus.cli import _handle_generate_context


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def gen_ctx_env(tmp_path: Path) -> dict:
    """Minimal filesystem for generate-context tests.

    Creates:
      - A module directory to document
      - An action prompt file
      - Patches PROMPTS_DIR to point to the temp tree
    """
    prompts_dir = tmp_path / "prompts"
    actions_dir = prompts_dir / "actions"
    actions_dir.mkdir(parents=True)

    action_prompt = actions_dir / "generate-context.md"
    action_prompt.write_text(
        "# generate-context\n\n"
        "ANALYZER -> GENERATOR -> VALIDATOR\n"
    )

    roles_dir = prompts_dir / "roles" / "generate-context"
    roles_dir.mkdir(parents=True)
    for role in ("analyzer", "generator", "validator"):
        (roles_dir / f"{role}.md").write_text(f"# {role} role stub\n")

    module_dir = tmp_path / "src" / "auth"
    module_dir.mkdir(parents=True)
    (module_dir / "models.py").write_text("class User: pass\n")
    (module_dir / "views.py").write_text("def login(): pass\n")

    return {
        "tmp_path": tmp_path,
        "prompts_dir": prompts_dir,
        "action_prompt": action_prompt,
        "module_dir": module_dir,
        "module_path": str(module_dir),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_generate_context(
    sub_args: list[str],
    prompts_dir: Path,
    *,
    project_context: str = "",
    claude_returncode: int = 0,
    project_root: Path | None = None,
) -> tuple[MagicMock, str, str]:
    """Run _handle_generate_context with all external boundaries stubbed.

    Returns (subprocess_mock, captured_stdout, captured_stderr).
    """
    mock_result = MagicMock()
    mock_result.returncode = claude_returncode

    with (
        patch("cplus.cli.PROMPTS_DIR", prompts_dir),
        patch("cplus.cli._check_claude"),
        patch("cplus.cli._get_project_context", return_value=project_context),
        patch("cplus.cli.find_project_root", return_value=project_root),
        patch("cplus.cli.subprocess.run", return_value=mock_result) as mock_run,
        patch("cplus.cli.sys.exit") as mock_exit,
    ):
        _handle_generate_context(sub_args)

    return mock_run, mock_exit


# ---------------------------------------------------------------------------
# Tests: happy path
# ---------------------------------------------------------------------------

class TestGenerateContextHappyPath:
    """Full run with valid module path and stubbed claude."""

    def test_invokes_claude_with_composed_prompt(self, gen_ctx_env: dict) -> None:
        mock_run, mock_exit = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
        )

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.args[0] == ["claude"]
        assert call_kwargs.kwargs["text"] is True

        composed = call_kwargs.kwargs["input"]
        assert "generate-context" in composed
        assert "ANALYZER" in composed
        assert f'`{gen_ctx_env["module_path"]}`' in composed

    def test_prompt_includes_module_path(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
        )

        composed = mock_run.call_args.kwargs["input"]
        assert "### Additional Instructions" in composed
        assert f"**Module path**: `{gen_ctx_env['module_path']}`" in composed

    def test_prompt_includes_project_root(self, gen_ctx_env: dict) -> None:
        root = gen_ctx_env["tmp_path"]
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
            project_root=root,
        )

        composed = mock_run.call_args.kwargs["input"]
        assert f"**Project root**: `{root}`" in composed

    def test_prompt_uses_cwd_when_no_project_root(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
            project_root=None,
        )

        composed = mock_run.call_args.kwargs["input"]
        assert "**Project root**:" in composed

    def test_exits_with_claude_return_code(self, gen_ctx_env: dict) -> None:
        _, mock_exit = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
            claude_returncode=0,
        )
        mock_exit.assert_called_once_with(0)

    def test_propagates_nonzero_exit_code(self, gen_ctx_env: dict) -> None:
        _, mock_exit = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
            claude_returncode=1,
        )
        mock_exit.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# Tests: --dry-run flag
# ---------------------------------------------------------------------------

class TestGenerateContextDryRun:
    """Verify --dry-run adds the mode marker to the composed prompt."""

    def test_dry_run_adds_mode_to_prompt(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"], "--dry-run"],
            gen_ctx_env["prompts_dir"],
        )

        composed = mock_run.call_args.kwargs["input"]
        assert "**Mode**: dry-run" in composed
        assert "stop after ANALYZER phase" in composed

    def test_dry_run_flag_before_path(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            ["--dry-run", gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
        )

        composed = mock_run.call_args.kwargs["input"]
        assert "**Mode**: dry-run" in composed
        assert f'`{gen_ctx_env["module_path"]}`' in composed

    def test_no_dry_run_omits_mode(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
        )

        composed = mock_run.call_args.kwargs["input"]
        assert "dry-run" not in composed


# ---------------------------------------------------------------------------
# Tests: project context injection
# ---------------------------------------------------------------------------

class TestGenerateContextProjectContext:
    """Verify project context is injected into the composed prompt."""

    def test_project_context_included(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
            project_context="### Project\nname: myproj\ntest: pytest\n",
        )

        composed = mock_run.call_args.kwargs["input"]
        assert "name: myproj" in composed
        assert "test: pytest" in composed

    def test_empty_project_context_not_injected(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
            project_context="",
        )

        composed = mock_run.call_args.kwargs["input"]
        # Action prompt + additional instructions, no project section
        assert "### Additional Instructions" in composed
        # Prompt should start with action content, not a blank project block
        lines = composed.strip().split("\n")
        assert lines[0] == "# generate-context"


# ---------------------------------------------------------------------------
# Tests: error paths
# ---------------------------------------------------------------------------

class TestGenerateContextErrors:
    """Verify error handling for bad inputs."""

    def test_missing_module_path(self, gen_ctx_env: dict) -> None:
        with pytest.raises(SystemExit):
            with (
                patch("cplus.cli.PROMPTS_DIR", gen_ctx_env["prompts_dir"]),
                patch("cplus.cli._check_claude"),
                patch("cplus.cli._get_project_context", return_value=""),
                patch("cplus.cli.find_project_root", return_value=None),
            ):
                _handle_generate_context([])

    def test_nonexistent_module_path(self, gen_ctx_env: dict) -> None:
        with pytest.raises(SystemExit):
            with (
                patch("cplus.cli.PROMPTS_DIR", gen_ctx_env["prompts_dir"]),
                patch("cplus.cli._check_claude"),
                patch("cplus.cli._get_project_context", return_value=""),
            ):
                _handle_generate_context(["/nonexistent/path"])

    def test_module_path_is_file_not_dir(self, gen_ctx_env: dict) -> None:
        file_path = gen_ctx_env["tmp_path"] / "not_a_dir.txt"
        file_path.write_text("hello")

        with pytest.raises(SystemExit):
            with (
                patch("cplus.cli.PROMPTS_DIR", gen_ctx_env["prompts_dir"]),
                patch("cplus.cli._check_claude"),
                patch("cplus.cli._get_project_context", return_value=""),
            ):
                _handle_generate_context([str(file_path)])

    def test_unknown_option(self, gen_ctx_env: dict) -> None:
        with pytest.raises(SystemExit):
            with (
                patch("cplus.cli.PROMPTS_DIR", gen_ctx_env["prompts_dir"]),
                patch("cplus.cli._check_claude"),
                patch("cplus.cli._get_project_context", return_value=""),
            ):
                _handle_generate_context(["--bogus", gen_ctx_env["module_path"]])

    def test_duplicate_module_path(self, gen_ctx_env: dict) -> None:
        with pytest.raises(SystemExit):
            with (
                patch("cplus.cli.PROMPTS_DIR", gen_ctx_env["prompts_dir"]),
                patch("cplus.cli._check_claude"),
                patch("cplus.cli._get_project_context", return_value=""),
            ):
                _handle_generate_context([
                    gen_ctx_env["module_path"],
                    gen_ctx_env["module_path"],
                ])

    def test_missing_action_prompt(self, tmp_path: Path) -> None:
        """Action prompt file doesn't exist in prompts dir."""
        empty_prompts = tmp_path / "prompts"
        empty_prompts.mkdir()
        (empty_prompts / "actions").mkdir()

        module_dir = tmp_path / "mod"
        module_dir.mkdir()

        with pytest.raises(SystemExit):
            with (
                patch("cplus.cli.PROMPTS_DIR", empty_prompts),
                patch("cplus.cli._check_claude"),
                patch("cplus.cli._get_project_context", return_value=""),
            ):
                _handle_generate_context([str(module_dir)])


# ---------------------------------------------------------------------------
# Tests: --help flag
# ---------------------------------------------------------------------------

class TestGenerateContextHelp:
    """Verify --help prints usage and returns without calling claude."""

    def test_help_flag(self, gen_ctx_env: dict, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("cplus.cli.PROMPTS_DIR", gen_ctx_env["prompts_dir"]),
            patch("cplus.cli.subprocess.run") as mock_run,
        ):
            _handle_generate_context(["--help"])

        mock_run.assert_not_called()
        captured = capsys.readouterr()
        assert "Usage: cplus generate-context" in captured.out
        assert "module-path" in captured.out

    def test_h_flag(self, gen_ctx_env: dict, capsys: pytest.CaptureFixture[str]) -> None:
        with (
            patch("cplus.cli.PROMPTS_DIR", gen_ctx_env["prompts_dir"]),
            patch("cplus.cli.subprocess.run") as mock_run,
        ):
            _handle_generate_context(["-h"])

        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: prompt composition order
# ---------------------------------------------------------------------------

class TestGenerateContextPromptComposition:
    """Verify the composed prompt has correct section ordering."""

    def test_prompt_section_order(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
            project_context="### Project\nname: test-proj\n",
        )

        composed = mock_run.call_args.kwargs["input"]

        # Action prompt comes first
        action_idx = composed.index("# generate-context")
        # Project context comes after action
        project_idx = composed.index("name: test-proj")
        # Additional instructions come last
        instructions_idx = composed.index("### Additional Instructions")

        assert action_idx < project_idx < instructions_idx

    def test_action_prompt_content_preserved(self, gen_ctx_env: dict) -> None:
        mock_run, _ = _run_generate_context(
            [gen_ctx_env["module_path"]],
            gen_ctx_env["prompts_dir"],
        )

        composed = mock_run.call_args.kwargs["input"]
        assert "ANALYZER -> GENERATOR -> VALIDATOR" in composed
