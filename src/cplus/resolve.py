"""Fuzzy matching, fzf integration, interactive selection."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _find_prompts(directory: Path) -> list[Path]:
    """Find all .md files recursively in a directory."""
    if not directory.is_dir():
        return []
    return sorted(directory.rglob("*.md"))


def _name_from_path(file: Path, base_dir: Path) -> str:
    """Get the display name (relative path without .md) for a prompt file."""
    return str(file.relative_to(base_dir)).removesuffix(".md")


def _check_fzf() -> None:
    """Verify fzf is available."""
    try:
        subprocess.run(["fzf", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: fzf is required for interactive selection", file=sys.stderr)
        print("Install with: brew install fzf", file=sys.stderr)
        sys.exit(1)


def _fzf_select(items: list[str], prompt: str, multi: bool = False) -> list[str]:
    """Run fzf for interactive selection."""
    _check_fzf()
    if not items:
        return []

    args = ["fzf", "--prompt", prompt, "--height=40%", "--reverse"]
    if multi:
        args.append("--multi")

    result = subprocess.run(
        args,
        input="\n".join(items),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 or not result.stdout.strip():
        return []

    return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]


def fuzzy_match_prompt(selector: str, directory: Path) -> Path | None:
    """Match a selector to a prompt file.

    Order: file path check -> exact name -> substring match.
    Returns None if no match or ambiguous.
    """
    # Check if selector is an existing file path
    as_path = Path(selector)
    if as_path.is_file():
        return as_path

    # Try exact match
    exact = directory / f"{selector}.md"
    if exact.is_file():
        return exact

    # Try substring match
    all_files = _find_prompts(directory)
    matches = []
    for f in all_files:
        name = _name_from_path(f, directory)
        if selector in name:
            matches.append(f)

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Ambiguous selector '{selector}' matches multiple files:", file=sys.stderr)
        for m in matches:
            print(f"  {m}", file=sys.stderr)
        return None

    return None


def resolve_action(selector: str | None, prompts_dir: Path) -> Path:
    """Resolve an action prompt.

    If selector given: fuzzy match in actions dir.
    If no selector: interactive fzf selection.
    Exits on failure.
    """
    actions_dir = prompts_dir / "actions"

    # If selector is a file path, use it directly
    if selector and Path(selector).is_file():
        return Path(selector)

    # If selector provided, fuzzy match
    if selector:
        result = fuzzy_match_prompt(selector, actions_dir)
        if result is not None:
            return result
        print(f"Error: Could not resolve action prompt '{selector}'", file=sys.stderr)
        sys.exit(1)

    # Interactive selection
    all_files = _find_prompts(actions_dir)
    if not all_files:
        print(f"No action prompts found in {actions_dir}", file=sys.stderr)
        sys.exit(1)

    names = [_name_from_path(f, actions_dir) for f in all_files]
    selected = _fzf_select(names, "Select action: ")

    if not selected:
        print("No action selected", file=sys.stderr)
        sys.exit(1)

    return actions_dir / f"{selected[0]}.md"


def resolve_roles(selectors: list[str], prompts_dir: Path) -> list[Path]:
    """Resolve role prompts from selectors.

    If selectors given: fuzzy match each.
    If empty: interactive fzf multi-selection.
    Exits on failure.
    """
    roles_dir = prompts_dir / "roles"

    if not selectors:
        # Interactive multi-selection
        all_files = _find_prompts(roles_dir)
        if not all_files:
            return []

        names = [_name_from_path(f, roles_dir) for f in all_files]
        selected = _fzf_select(names, "Select roles (tab to select multiple, enter to confirm): ",
                                multi=True)
        return [roles_dir / f"{name}.md" for name in selected]

    # Resolve each selector
    resolved = []
    for sel in selectors:
        result = fuzzy_match_prompt(sel, roles_dir)
        if result is not None:
            resolved.append(result)
        else:
            print(f"Error: Could not resolve role '{sel}'", file=sys.stderr)
            sys.exit(1)

    return resolved
