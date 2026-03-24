"""Tests for resolve module."""

from pathlib import Path

from cplus.resolve import fuzzy_match_prompt


def _setup_actions(tmp_path: Path) -> Path:
    """Create a fake actions directory with some prompts."""
    actions = tmp_path / "actions"
    actions.mkdir()
    (actions / "spec.md").write_text("spec prompt")
    (actions / "develop.md").write_text("develop prompt")
    (actions / "develop-v2.md").write_text("develop-v2 prompt")
    (actions / "develop-v3.md").write_text("develop-v3 prompt")
    (actions / "review.md").write_text("review prompt")
    return actions


def test_exact_match(tmp_path: Path) -> None:
    actions = _setup_actions(tmp_path)
    result = fuzzy_match_prompt("spec", actions)
    assert result == actions / "spec.md"


def test_file_path_match(tmp_path: Path) -> None:
    actions = _setup_actions(tmp_path)
    result = fuzzy_match_prompt(str(actions / "spec.md"), actions)
    assert result == actions / "spec.md"


def test_substring_unique_match(tmp_path: Path) -> None:
    actions = _setup_actions(tmp_path)
    result = fuzzy_match_prompt("rev", actions)
    assert result == actions / "review.md"


def test_exact_match_wins_over_substring(tmp_path: Path) -> None:
    actions = _setup_actions(tmp_path)
    # "develop" exact-matches develop.md even though substring would match 3 files
    result = fuzzy_match_prompt("develop", actions)
    assert result == actions / "develop.md"


def test_substring_ambiguous_match(tmp_path: Path) -> None:
    actions = _setup_actions(tmp_path)
    # "dev" substring-matches develop.md, develop-v2.md, develop-v3.md
    result = fuzzy_match_prompt("dev", actions)
    assert result is None  # Ambiguous


def test_no_match(tmp_path: Path) -> None:
    actions = _setup_actions(tmp_path)
    result = fuzzy_match_prompt("nonexistent", actions)
    assert result is None


def test_exact_match_preferred_over_substring(tmp_path: Path) -> None:
    """Exact name match should work even if substring would also match."""
    actions = _setup_actions(tmp_path)
    result = fuzzy_match_prompt("spec", actions)
    assert result == actions / "spec.md"
