"""Project context detection and .cplus.yml parsing."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


PROJECT_MARKERS = (
    ".cplus.yml",
    ".git/config",
    "package.json",
    "Makefile",
    "go.mod",
    "Cargo.toml",
)


@dataclass
class ProjectContext:
    root: Path
    name: str
    config_source: str  # ".cplus.yml" | "package.json" | "Makefile"
    commands: dict[str, str] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    conventions: list[str] = field(default_factory=list)


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk up directory tree looking for project markers."""
    current = (start or Path.cwd()).resolve()
    while True:
        for marker in PROJECT_MARKERS:
            if (current / marker).exists():
                return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _parse_cplus_yml(config_file: Path) -> ProjectContext:
    """Parse a .cplus.yml config into ProjectContext."""
    data = yaml.safe_load(config_file.read_text())
    if not isinstance(data, dict):
        data = {}

    project = data.get("project", {}) or {}
    name = project.get("name", config_file.parent.name)
    # Strip quotes if present
    if isinstance(name, str):
        name = name.strip('"').strip("'")

    commands = {}
    raw_commands = data.get("commands", {}) or {}
    for k, v in raw_commands.items():
        if isinstance(v, str):
            commands[k] = v.strip('"').strip("'")

    paths = {}
    raw_paths = data.get("paths", {}) or {}
    for k, v in raw_paths.items():
        if isinstance(v, str):
            paths[k] = v.strip('"').strip("'")

    conventions = []
    raw_conventions = data.get("conventions", []) or []
    for item in raw_conventions:
        if isinstance(item, str):
            conventions.append(item.strip('"').strip("'"))

    return ProjectContext(
        root=config_file.parent,
        name=name,
        config_source=".cplus.yml",
        commands=commands,
        paths=paths,
        conventions=conventions,
    )


def _parse_package_json(pkg_file: Path) -> ProjectContext:
    """Parse package.json scripts into ProjectContext."""
    data = json.loads(pkg_file.read_text())
    scripts = data.get("scripts", {})
    commands = {k: v for k, v in scripts.items() if isinstance(v, str)}
    name = data.get("name", pkg_file.parent.name)

    return ProjectContext(
        root=pkg_file.parent,
        name=name,
        config_source="package.json",
        commands=commands,
    )


def _parse_makefile(makefile: Path) -> ProjectContext:
    """Parse Makefile targets into ProjectContext."""
    text = makefile.read_text()
    targets = re.findall(r"^([a-zA-Z0-9_-]+):", text, re.MULTILINE)
    commands = {t: f"make {t}" for t in targets}

    return ProjectContext(
        root=makefile.parent,
        name=makefile.parent.name,
        config_source="Makefile",
        commands=commands,
    )


def detect_project(start: Path | None = None) -> ProjectContext | None:
    """Detect project root and load config."""
    root = find_project_root(start)
    if root is None:
        return None

    cplus_yml = root / ".cplus.yml"
    if cplus_yml.is_file():
        return _parse_cplus_yml(cplus_yml)

    pkg_json = root / "package.json"
    if pkg_json.is_file():
        return _parse_package_json(pkg_json)

    makefile = root / "Makefile"
    if makefile.is_file():
        return _parse_makefile(makefile)

    # Project root found via other marker (.git, go.mod, etc.) but no config
    return None


def format_project_context(ctx: ProjectContext) -> str:
    """Format ProjectContext as markdown matching zsh output."""
    lines: list[str] = []
    lines.append("")
    lines.append("### Project Context")
    lines.append("")
    lines.append(f"**Project**: {ctx.name}")
    lines.append("")

    if ctx.commands:
        lines.append("**Commands**:")
        for name, cmd in ctx.commands.items():
            lines.append(f"- {name}: `{cmd}`")

    if ctx.paths:
        lines.append("")
        lines.append("**Paths**:")
        for name, path in ctx.paths.items():
            lines.append(f"- {name}: `{path}`")

    if ctx.conventions:
        lines.append("")
        lines.append("**Conventions**:")
        for conv in ctx.conventions:
            lines.append(f"- {conv}")

    return "\n".join(lines)
