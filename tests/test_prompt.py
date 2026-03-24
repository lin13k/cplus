"""Tests for prompt module."""

from pathlib import Path

from cplus.prompt import compose_prompt


def test_compose_base_only(tmp_path: Path) -> None:
    base = tmp_path / "action.md"
    base.write_text("# Base Action\nDo the thing.")
    result = compose_prompt(base, [], "", [])
    assert "# Base Action" in result
    assert "Do the thing." in result


def test_compose_with_roles(tmp_path: Path) -> None:
    base = tmp_path / "action.md"
    base.write_text("base content")
    role1 = tmp_path / "architect.md"
    role1.write_text("You are an architect.")
    role2 = tmp_path / "reviewer.md"
    role2.write_text("You are a reviewer.")

    result = compose_prompt(base, [role1, role2], "", [])
    assert "### Roles" in result
    assert "#### architect" in result
    assert "You are an architect." in result
    assert "#### reviewer" in result
    assert "You are a reviewer." in result


def test_compose_with_project_context(tmp_path: Path) -> None:
    base = tmp_path / "action.md"
    base.write_text("base content")
    ctx = "\n### Project Context\n\n**Project**: myproj\n"

    result = compose_prompt(base, [], ctx, [])
    assert "### Project Context" in result
    assert "**Project**: myproj" in result


def test_compose_with_extras_text(tmp_path: Path) -> None:
    base = tmp_path / "action.md"
    base.write_text("base content")

    result = compose_prompt(base, [], "", ["be strict"])
    assert "### Additional Instructions" in result
    assert "#### text" in result
    assert "be strict" in result


def test_compose_with_extras_file(tmp_path: Path) -> None:
    base = tmp_path / "action.md"
    base.write_text("base content")
    extra_file = tmp_path / "notes.md"
    extra_file.write_text("important notes")

    result = compose_prompt(base, [], "", [extra_file])
    assert f"#### file: {extra_file}" in result
    assert "important notes" in result


def test_compose_full(tmp_path: Path) -> None:
    base = tmp_path / "action.md"
    base.write_text("# Action\n")
    role = tmp_path / "arch.md"
    role.write_text("architect role")
    ctx = "\n### Project Context\n\n**Project**: test\n"

    result = compose_prompt(base, [role], ctx, ["extra text"])
    # Verify ordering: base -> roles -> context -> extras
    base_idx = result.index("# Action")
    roles_idx = result.index("### Roles")
    ctx_idx = result.index("### Project Context")
    extras_idx = result.index("### Additional Instructions")
    assert base_idx < roles_idx < ctx_idx < extras_idx
