"""CLI entry point - all cplus commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from cplus.config import detect_project, find_project_root, format_project_context
from cplus.prompt import compose_prompt
from cplus.resolve import resolve_action, resolve_roles


# --- Prompts directory resolution ---

def _find_prompts_dir() -> Path:
    """Find prompts directory: script-relative first, then ~/.config/cplus/prompts/."""
    pkg_dir = Path(__file__).resolve().parent
    repo_prompts = pkg_dir.parent.parent / "prompts"
    if repo_prompts.is_dir():
        return repo_prompts

    config_prompts = Path.home() / ".config" / "cplus" / "prompts"
    if config_prompts.is_dir():
        return config_prompts

    return repo_prompts


PROMPTS_DIR = _find_prompts_dir()

KNOWN_OPERATIONS = {
    "run", "pick", "ls", "role", "project", "develop-v3",
    "setup-worktree", "cleanup-worktree", "help", "version",
}


# --- Arg parsing ---

def _parse_args(argv: list[str]) -> dict:
    """Parse CLI args matching zsh behavior."""
    args = list(argv)
    result = {
        "operation": "run",
        "selector": None,
        "roles": None,
        "model": None,
        "dry_run": False,
        "print_mode": False,
        "skip_permissions": False,
        "output_file": None,
        "extras": [],
        "sub_args": [],
    }

    if not args:
        return result

    # First arg: operation or selector
    if args[0] in KNOWN_OPERATIONS or args[0] in ("--help", "-h"):
        result["operation"] = args.pop(0)
    # Handle --help/-h
    if result["operation"] in ("--help", "-h"):
        result["operation"] = "help"
        return result

    # For ls, project, develop-v3, setup-worktree, cleanup-worktree: rest is sub_args
    if result["operation"] in ("ls", "project", "develop-v3", "setup-worktree", "cleanup-worktree"):
        result["sub_args"] = args
        return result

    # Parse remaining args
    while args:
        arg = args[0]
        if arg == "--roles":
            args.pop(0)
            if not args:
                print("Error: --roles requires an argument", file=sys.stderr)
                sys.exit(1)
            result["roles"] = args.pop(0)
        elif arg.startswith("--roles="):
            result["roles"] = arg[len("--roles="):]
            args.pop(0)
        elif arg == "--dry-run":
            result["dry_run"] = True
            args.pop(0)
        elif arg in ("-p", "--print"):
            result["print_mode"] = True
            args.pop(0)
        elif arg == "--output-file":
            args.pop(0)
            if not args:
                print("Error: --output-file requires a path", file=sys.stderr)
                sys.exit(1)
            result["output_file"] = args.pop(0)
        elif arg == "--model":
            args.pop(0)
            if not args:
                print("Error: --model requires a value", file=sys.stderr)
                sys.exit(1)
            result["model"] = args.pop(0)
        elif arg.startswith("--model="):
            result["model"] = arg[len("--model="):]
            args.pop(0)
        elif arg == "--dangerously-skip-permissions":
            result["skip_permissions"] = True
            args.pop(0)
        elif arg in ("--help", "-h"):
            result["operation"] = "help"
            args.pop(0)
            return result
        elif arg.startswith("-"):
            print(f"Error: Unknown option {arg}", file=sys.stderr)
            sys.exit(1)
        else:
            if result["operation"] == "pick":
                result["extras"].append(arg)
            elif result["selector"] is None:
                result["selector"] = arg
            else:
                result["extras"].append(arg)
            args.pop(0)

    return result


# --- Helpers ---

def _parse_roles_list(roles: str | None) -> list[str]:
    if not roles:
        return []
    return [r.strip() for r in roles.split(",") if r.strip()]


def _check_claude() -> None:
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: 'claude' command not found in PATH", file=sys.stderr)
        print("Please ensure Claude CLI is installed and available", file=sys.stderr)
        sys.exit(1)


def _get_project_context() -> str:
    ctx = detect_project()
    if ctx is None:
        return ""
    return format_project_context(ctx)


# --- Operations ---

def _handle_run_or_pick(parsed: dict) -> None:
    force_interactive = parsed["operation"] == "pick"
    selector = None if force_interactive else parsed["selector"]
    base_file = resolve_action(selector, PROMPTS_DIR)

    role_files: list[Path] = []
    if parsed["roles"] is not None:
        role_selectors = _parse_roles_list(parsed["roles"])
        role_files = resolve_roles(role_selectors, PROMPTS_DIR)

    project_context = _get_project_context()
    prompt_text = compose_prompt(base_file, role_files, project_context, parsed["extras"])

    if parsed["output_file"]:
        prompt_text += (
            "\n\n### Output Requirement\n"
            f"Write your JSON output to the file: {parsed['output_file']}\n"
            "Do NOT print the JSON to the conversation. "
            "Write ONLY the raw JSON object to the file — no markdown fences, no prose, no explanation.\n"
        )

    if parsed["dry_run"]:
        print(prompt_text)
        return

    _check_claude()

    if parsed["print_mode"]:
        cmd = ["claude", "-p"]
        if parsed["skip_permissions"]:
            cmd.append("--dangerously-skip-permissions")
        if parsed["model"]:
            cmd.extend(["--model", parsed["model"]])
        result = subprocess.run(cmd, input=prompt_text, text=True)
        sys.exit(result.returncode)
    else:
        cmd = ["claude"]
        if parsed["model"]:
            cmd.extend(["--model", parsed["model"]])
        result = subprocess.run(cmd, input=prompt_text, text=True)
        sys.exit(result.returncode)


def _handle_ls(sub_args: list[str]) -> None:
    subcommand = sub_args[0] if sub_args else None
    actions_dir = PROMPTS_DIR / "actions"
    roles_dir = PROMPTS_DIR / "roles"

    def list_actions() -> None:
        if not actions_dir.is_dir():
            print(f"No actions directory found at {actions_dir}", file=sys.stderr)
            sys.exit(1)
        print("Available actions:")
        for f in sorted(actions_dir.rglob("*.md")):
            name = str(f.relative_to(actions_dir)).removesuffix(".md")
            print(f"  {name}")

    def list_roles() -> None:
        if not roles_dir.is_dir():
            print(f"No roles directory found at {roles_dir}", file=sys.stderr)
            sys.exit(1)
        print("Available roles:")
        for f in sorted(roles_dir.rglob("*.md")):
            name = str(f.relative_to(roles_dir)).removesuffix(".md")
            print(f"  {name}")

    if subcommand == "actions":
        list_actions()
    elif subcommand == "roles":
        list_roles()
    elif subcommand is None:
        list_actions()
        print()
        list_roles()
    else:
        print(f"Unknown ls subcommand: {subcommand}", file=sys.stderr)
        print("Usage: cplus ls [actions|roles]", file=sys.stderr)
        sys.exit(1)


def _handle_role(sub_args: list[str]) -> None:
    roles_str = None
    args = list(sub_args)
    while args:
        if args[0] == "--roles":
            args.pop(0)
            if not args:
                print("Error: --roles requires an argument", file=sys.stderr)
                sys.exit(1)
            roles_str = args.pop(0)
        elif args[0].startswith("--roles="):
            roles_str = args[0][len("--roles="):]
            args.pop(0)
        else:
            print(f"Error: Unknown argument for role operation: {args[0]}", file=sys.stderr)
            sys.exit(1)

    role_selectors = _parse_roles_list(roles_str)
    resolved = resolve_roles(role_selectors, PROMPTS_DIR)

    if resolved:
        print("Resolved roles:")
        for role_file in resolved:
            print(f"  {role_file}")
    else:
        print("No roles selected")


def _handle_project(sub_args: list[str]) -> None:
    subcommand = sub_args[0] if sub_args else "show"

    if subcommand == "show":
        root = find_project_root()
        if root is None:
            print("No project detected in current directory or parents")
            print()
            print("Looked for: .cplus.yml, .git/, package.json, Makefile, go.mod, Cargo.toml")
            print()
            print("Run 'cplus project init' to create a .cplus.yml config")
            sys.exit(1)

        print(f"Project root: {root}")
        print()

        cplus_yml = root / ".cplus.yml"
        pkg_json = root / "package.json"
        makefile = root / "Makefile"

        if cplus_yml.is_file():
            print("Config: .cplus.yml (explicit config)")
            print()
            print(cplus_yml.read_text(), end="")
        elif pkg_json.is_file():
            print("Config: package.json (auto-detected)")
            print()
            print("Commands (from package.json scripts):")
            ctx = detect_project(root)
            if ctx:
                for name, cmd in ctx.commands.items():
                    print(f"  {name}: {cmd}")
        elif makefile.is_file():
            print("Config: Makefile (auto-detected)")
            print()
            print("Commands (from Makefile targets):")
            ctx = detect_project(root)
            if ctx:
                for name, cmd in ctx.commands.items():
                    print(f"  {name}: {cmd}")
        else:
            print("Project detected but no recognized config file")

    elif subcommand == "init":
        if Path(".cplus.yml").exists():
            print("Error: .cplus.yml already exists in current directory", file=sys.stderr)
            sys.exit(1)

        template = """\
# cplus project configuration
project:
  name: "my-project"
  description: "Project description"

commands:
  # Testing
  test: "npm test"
  test_file: "npm test --"

  # Build & Type Check
  build: "npm run build"
  type_check: "npm run type-check"
  lint: "npm run lint"

  # Development
  dev: "npm run dev"
  install: "npm install"

paths:
  src: "src/"
  tests: "tests/"
  config: "./"

conventions:
  - "Add your project-specific conventions here"
  - "These will be shown to Claude when composing prompts"
"""
        Path(".cplus.yml").write_text(template)
        print("Created .cplus.yml")
        print()
        print("Edit .cplus.yml to customize for your project.")
        print("Run 'cplus project show' to see the detected config.")

    elif subcommand == "validate":
        root = find_project_root()
        if root is None:
            print("No project detected")
            sys.exit(1)

        print(f"Project root found: {root}")

        cplus_yml = root / ".cplus.yml"
        if cplus_yml.is_file():
            print(".cplus.yml found")
            text = cplus_yml.read_text()
            if "project:" in text and "commands:" in text:
                print("Config structure looks valid")
            else:
                print("Config may be malformed (missing project: or commands: section)")
        elif (root / "package.json").is_file():
            print("package.json found (auto-detected)")
        elif (root / "Makefile").is_file():
            print("Makefile found (auto-detected)")

        print()
        print("Project context will be injected into prompts automatically.")

    else:
        print(f"Unknown project subcommand: {subcommand}", file=sys.stderr)
        print("Usage: cplus project [show|init|validate]", file=sys.stderr)
        sys.exit(1)


def _handle_setup_worktree(sub_args: list[str]) -> None:
    """Handle: cplus setup-worktree <task-id> [--install-cmd <cmd>]"""
    from cplus.pipeline.git import setup_worktree

    task_id: str | None = None
    install_cmd: str | None = None
    args = list(sub_args)
    while args:
        if args[0] == "--install-cmd":
            args.pop(0)
            if not args:
                print("Error: --install-cmd requires a value", file=sys.stderr)
                sys.exit(1)
            install_cmd = args.pop(0)
        elif args[0].startswith("-"):
            print(f"Error: unknown option {args[0]}", file=sys.stderr)
            print("Usage: cplus setup-worktree <task-id> [--install-cmd <cmd>]", file=sys.stderr)
            sys.exit(1)
        else:
            task_id = args.pop(0)

    if not task_id:
        print("Error: task-id required", file=sys.stderr)
        print("Usage: cplus setup-worktree <task-id> [--install-cmd <cmd>]", file=sys.stderr)
        sys.exit(1)

    setup_worktree(task_id, install_cmd)


def _handle_cleanup_worktree(sub_args: list[str]) -> None:
    """Handle: cplus cleanup-worktree <task-id>"""
    from cplus.pipeline.git import cleanup_worktree

    if not sub_args or sub_args[0].startswith("-"):
        print("Error: task-id required", file=sys.stderr)
        print("Usage: cplus cleanup-worktree <task-id>", file=sys.stderr)
        sys.exit(1)

    cleanup_worktree(sub_args[0])



def _handle_version() -> None:
    """Print cplus version."""
    try:
        from importlib.metadata import PackageNotFoundError, version
        v = version("cplus")
    except PackageNotFoundError:
        v = "dev"
    print(f"cplus {v}")


def _handle_help() -> None:
    print("""\
cplus - Prompt composition tool for Claude CLI

SYNOPSIS
  cplus [operation] [prompt_selector] [options] [extras...]

OPERATIONS
  run (default)  Build a composed prompt and pipe it to claude
  pick           Force interactive selection of action prompt, then run
  ls             List available prompts and roles
  role           Resolve roles to files and print them
  project        Manage project configuration (show, init, validate)
  develop-v3     Automated multi-session pipeline (architect->setup->implement->verify->review->cleanup)
  help           Print this usage information

EXAMPLES
  cplus                                    # Interactive: pick action (no roles)
  cplus spec                               # Use 'spec' action (no roles)
  cplus develop --roles architect          # Use 'develop' with 'architect' role
  cplus pick --roles reviewer notes/DECISIONS.md
  cplus tasks/123/task.md "be strict"      # Use task file (no roles)
  cplus ls actions                         # List available actions
  cplus ls roles                           # List available roles
  cplus role --roles arch,review           # Print resolved role files
  cplus project show                       # Show detected project context
  cplus project init                       # Create .cplus.yml template
  cplus develop-v3 .cplus/specs/0001.md   # Run automated pipeline
  cplus develop-v3 spec.md --from verify  # Resume from verify phase

OPTIONS
  --roles <role1,role2,...>  Inject roles (comma-separated or repeated)
  --model <model>            Claude model to use (e.g. opus, sonnet, haiku)
  --dry-run                  Preview composition without sending to claude
  -p, --print                Non-interactive mode: pipe to claude -p and print output
  --help, -h                 Show this help message

NOTE
  By default, NO roles are injected. Use --roles to explicitly add role definitions.

For full specification, see cplus_contract.md""")


# --- Entry point ---

def app_entry() -> None:
    """Entry point for both pyproject.toml scripts and __main__.py."""
    parsed = _parse_args(sys.argv[1:])
    op = parsed["operation"]

    if op == "version":
        _handle_version()
    elif op == "help":
        _handle_help()
    elif op == "ls":
        _handle_ls(parsed["sub_args"])
    elif op == "role":
        _handle_role(parsed["sub_args"])
    elif op == "project":
        _handle_project(parsed["sub_args"])
    elif op == "develop-v3":
        from cplus.pipeline.orchestrator import run_develop_v3_cli
        run_develop_v3_cli(parsed["sub_args"], PROMPTS_DIR)
    elif op == "setup-worktree":
        _handle_setup_worktree(parsed["sub_args"])
    elif op == "cleanup-worktree":
        _handle_cleanup_worktree(parsed["sub_args"])
    elif op in ("run", "pick"):
        _handle_run_or_pick(parsed)
    else:
        print(f"Unknown operation: {op}", file=sys.stderr)
        sys.exit(1)
