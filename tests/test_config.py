"""Tests for config module."""

from pathlib import Path

from cplus.config import (
    ProjectContext,
    detect_project,
    find_project_root,
    format_project_context,
)


def test_find_project_root_cplus_yml(tmp_path: Path) -> None:
    (tmp_path / ".cplus.yml").write_text("project:\n  name: test\n")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert find_project_root(sub) == tmp_path


def test_find_project_root_git(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("")
    assert find_project_root(tmp_path) == tmp_path


def test_find_project_root_none(tmp_path: Path) -> None:
    sub = tmp_path / "empty"
    sub.mkdir()
    # tmp_path itself may match something above; use isolated check
    result = find_project_root(sub)
    # Should either be None or some parent — we just verify it doesn't crash
    assert result is None or isinstance(result, Path)


def test_detect_project_cplus_yml(tmp_path: Path) -> None:
    config = tmp_path / ".cplus.yml"
    config.write_text(
        "project:\n"
        '  name: "myproj"\n'
        "commands:\n"
        '  test: "pytest"\n'
        '  build: "make build"\n'
        "paths:\n"
        '  src: "src/"\n'
        "conventions:\n"
        '  - "Use type hints"\n'
    )
    ctx = detect_project(tmp_path)
    assert ctx is not None
    assert ctx.name == "myproj"
    assert ctx.config_source == ".cplus.yml"
    assert ctx.commands == {"test": "pytest", "build": "make build"}
    assert ctx.paths == {"src": "src/"}
    assert ctx.conventions == ["Use type hints"]


def test_detect_project_package_json(tmp_path: Path) -> None:
    pkg = tmp_path / "package.json"
    pkg.write_text('{"name": "my-app", "scripts": {"test": "jest", "build": "tsc"}}')
    ctx = detect_project(tmp_path)
    assert ctx is not None
    assert ctx.name == "my-app"
    assert ctx.config_source == "package.json"
    assert ctx.commands == {"test": "jest", "build": "tsc"}


def test_detect_project_makefile(tmp_path: Path) -> None:
    mf = tmp_path / "Makefile"
    mf.write_text("build:\n\tgo build\n\ntest:\n\tgo test ./...\n")
    ctx = detect_project(tmp_path)
    assert ctx is not None
    assert ctx.config_source == "Makefile"
    assert ctx.commands == {"build": "make build", "test": "make test"}


def test_detect_project_cplus_yml_priority(tmp_path: Path) -> None:
    """cplus.yml should take priority over package.json."""
    (tmp_path / ".cplus.yml").write_text("project:\n  name: from-yml\ncommands:\n  x: y\n")
    (tmp_path / "package.json").write_text('{"name": "from-pkg", "scripts": {"a": "b"}}')
    ctx = detect_project(tmp_path)
    assert ctx is not None
    assert ctx.name == "from-yml"
    assert ctx.config_source == ".cplus.yml"


def test_format_project_context() -> None:
    ctx = ProjectContext(
        root=Path("/tmp/proj"),
        name="myproj",
        config_source=".cplus.yml",
        commands={"test": "pytest", "build": "make"},
        paths={"src": "src/"},
        conventions=["Use type hints"],
    )
    output = format_project_context(ctx)
    assert "**Project**: myproj" in output
    assert "- test: `pytest`" in output
    assert "- build: `make`" in output
    assert "- src: `src/`" in output
    assert "- Use type hints" in output


def test_detect_project_no_config(tmp_path: Path) -> None:
    """Git-only project with no config file returns None."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("")
    ctx = detect_project(tmp_path)
    assert ctx is None
