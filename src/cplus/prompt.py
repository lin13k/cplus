"""Prompt composition: base + roles + project context + extras."""

from __future__ import annotations

from pathlib import Path


def compose_prompt(
    base_file: Path,
    role_files: list[Path],
    project_context: str,
    extras: list[str | Path],
) -> str:
    """Compose a full prompt from parts.

    Output structure matches zsh version exactly:
    1. Base prompt content
    2. ### Roles section (if roles provided)
    3. ### Project Context section (if project detected)
    4. ### Additional Instructions section (if extras provided)
    """
    parts: list[str] = []

    # Base prompt
    parts.append(base_file.read_text())

    # Roles section
    if role_files:
        parts.append("")
        parts.append("### Roles")
        for role_file in role_files:
            if role_file.is_file():
                role_name = role_file.stem
                parts.append(f"#### {role_name}")
                parts.append(role_file.read_text())
                parts.append("")

    # Project context (already formatted with ### heading)
    if project_context:
        parts.append(project_context)

    # Extras section
    if extras:
        parts.append("")
        parts.append("### Additional Instructions")
        for extra in extras:
            extra_path = Path(str(extra))
            if extra_path.is_file():
                parts.append(f"#### file: {extra}")
                parts.append(extra_path.read_text())
            else:
                parts.append("#### text")
                parts.append(str(extra))
            parts.append("")

    return "\n".join(parts)
