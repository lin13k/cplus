# cplus

Prompt composition tool for [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli). Build complex prompts from reusable actions and roles.

Optionally integrates with [Everything Claude Code (ECC)](https://github.com/affaan-m/everything-claude-code) for TDD, code review, security scanning, and verification workflows.

## Features

- **Composable prompts** - Build from reusable actions and roles
- **Project context** - Auto-inject project commands from `.cplus.yml`, `package.json`, or `Makefile`
- **Fuzzy matching** - Quick access without typing full names
- **Flexible context** - Attach files and text as needed
- **Interactive selection** - fzf integration when you need it
- **ECC integration** - `develop-v2` action delegates to ECC commands while cplus controls scope

## Quick Start

```bash
git clone https://github.com/lin13k/cplus.git
cd cplus
./install.sh                             # or: ./install.sh --with-ecc
```

### Structured workflows — the core of cplus

The biggest problem with AI agents on complex tasks: they lose focus, skip steps, and mix concerns. cplus solves this with **phased execution** — each phase has strict boundaries on what Claude can and cannot do.

```bash
# Spec out a feature through guided discovery
# Claude walks through 4 phases: DISCOVERER → SPECIFIER → VALIDATOR → REFINER
# It can't jump to solutions — it has to gather examples and constraints first
cplus spec "SSO integration with Google and GitHub OAuth"

# Develop it end-to-end from the spec
# 6 phases: ARCHITECT → SETUP → IMPLEMENTER → VERIFIER → REVIEWER → CLEANUP
# Architect can't write code. Implementer works one checkpoint at a time.
# Verifier can't fix bugs — only document them. No skipping phases.
cplus develop .cplus/specs/0001-sso-integration.md

# develop-v2: same phased control, but delegates to ECC commands
# IMPLEMENTER → /tdd, VERIFIER → /verify, REVIEWER → /code-review + /security-scan
cplus develop-v2 .cplus/specs/0001-sso-integration.md
```

### Tell Claude what to do — in plain English

```bash
# Spec out a feature — your prompt becomes the task context
cplus spec "plan how to add SSO integration for our repository"

# Plan with the architect role
cplus plan --roles architect "add rate limiting to API"

# Implement something specific
cplus implement "add pagination to /api/users endpoint"

# Debug with an error log attached
cplus debug logs/error.txt "users getting 500 on login since yesterday"

# Review code with security focus
cplus review --roles reviewer "focus on auth and input validation"
```

Your quoted text and files get composed into the prompt alongside the action and roles.

### Compose files, text, and roles freely

```bash
# Attach a schema file + instructions + architect role — all composed into one prompt
cplus implement schema.sql "add migration for new user fields" --roles architect

# Attach multiple files
cplus review src/auth.ts src/middleware.ts "check for token expiry edge cases"

# Preview what gets sent to Claude (without actually sending)
cplus develop --dry-run

# Interactive action picker (fzf)
cplus pick

# List everything available
cplus ls actions
cplus ls roles
```

## Installation

**Prerequisites**: Python 3.10+, [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli), fzf (`brew install fzf`)

### Recommended: pipx

[pipx](https://pipx.pypa.io/) installs cplus in an isolated environment with its own dependencies, keeping your system Python clean.

```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install cplus
pipx install git+https://github.com/lin13k/cplus.git

# Copy prompts to config directory
mkdir -p ~/.config/cplus
cp -r $(pipx runpip cplus show -f cplus 2>/dev/null | head -1 | xargs dirname)/cplus/../../prompts ~/.config/cplus/ 2>/dev/null \
  || echo "Clone the repo and copy prompts manually: cp -r prompts ~/.config/cplus/"
```

Or from a local clone:

```bash
git clone https://github.com/lin13k/cplus.git
cd cplus
pipx install .
cp -r prompts ~/.config/cplus/
```

### Alternative: pip

```bash
git clone https://github.com/lin13k/cplus.git
cd cplus
pip install .
cp -r prompts ~/.config/cplus/
```

### Alternative: install.sh (handles everything)

```bash
git clone https://github.com/lin13k/cplus.git
cd cplus
./install.sh
```

This runs `pip install .` and copies prompts to `~/.config/cplus/` in one step.

### With ECC (for develop-v2)

```bash
./install.sh --with-ecc
```

This additionally installs ECC's rules, commands, agents, skills, and hooks into `~/.claude/`. If you want language-specific rules:

```bash
./install.sh --with-ecc --ecc-langs=typescript,python,golang
```

ECC source is cloned to `~/projects/everything-claude-code/` (set `ECC_DIR` to override).

### Upgrading

```bash
# pipx
pipx upgrade cplus
# or reinstall from latest
pipx install --force git+https://github.com/lin13k/cplus.git

# pip
pip install --upgrade git+https://github.com/lin13k/cplus.git
```

## Usage

### Basic Commands

```bash
cplus [action] [--roles role1,role2] [extras...]

# Examples
cplus spec                                # Use spec action (no roles)
cplus develop --roles architect           # Add architect role when needed
cplus develop tasks/1.md                  # Add file as context (no roles)
cplus review --roles reviewer "check security"  # Opt-in to reviewer role
cplus pick                                # Interactive selection
cplus ls                                  # List available prompts
```

### Operations

| Command | Description |
|---------|-------------|
| `run` (default) | Compose and pipe to Claude |
| `pick` | Interactive action selection |
| `ls [actions\|roles]` | List prompts |
| `project [show\|init]` | Manage project config |

### Prompt Structure

```
prompts/
├── actions/          # What to do (plan, implement, review, spec, develop, develop-v2, add, etc.)
└── roles/            # How to behave (architect, implementer, add/gatherer, etc.)
```

Actions define the task. Roles are **opt-in** - use them when you need specific behavior:

```bash
cplus spec                                # Just the spec action
cplus develop --roles architect           # Add architect role when needed
cplus review --roles reviewer,architect   # Multiple roles for different perspectives
```

### Workflows

**`spec`** - Multi-phase specification development (DISCOVERER → SPECIFIER → VALIDATOR → REFINER):
```bash
cplus spec
```
Creates detailed specifications through concrete examples and structured discovery.

**`develop`** - Complete development lifecycle (ARCHITECT → SETUP → IMPLEMENTER → VERIFIER → REVIEWER → CLEANUP):
```bash
cplus develop .cplus/specs/0001-feature-name.md
```
Orchestrates full implementation from specification to delivery.

**`develop-v2`** - ECC-integrated development lifecycle (requires ECC):
```bash
cplus develop-v2 .cplus/specs/0001-feature-name.md
```
Same phased workflow as `develop`, but delegates specialized work to ECC:
- IMPLEMENTER delegates each checkpoint to `/tdd` (with inline content, not file references)
- VERIFIER runs `/verify full`
- REVIEWER runs `/code-review` + `/security-scan`
- Strategic `/compact` at every phase transition

cplus controls scope and state. ECC commands execute within that scope. See [develop-v2 plan](docs/develop-v2-plan.md) for the full design rationale.

**`add`** - Guided creation of new actions or roles (GATHERER → GENERATOR → VALIDATOR):
```bash
cplus add                              # Full guided workflow
cplus add --roles add/gatherer         # Run only the discovery phase
```
Interactively collects requirements, generates a complete prompt file from scratch following canonical schemas and Claude Code best practices, then validates before saving.

**Full Workflow Example**:
```bash
# 1. Create specification
cplus spec

# 2. Develop from spec (pick one)
cplus develop .cplus/specs/0001-feature-name.md      # v1: self-contained
cplus develop-v2 .cplus/specs/0001-feature-name.md   # v2: uses ECC commands

# 3. Add a new action or role
cplus add
```

## Project Context

Create `.cplus.yml` in your project root to auto-inject commands and conventions:

```yaml
project:
  name: "my-app"

commands:
  test: "npm test"
  build: "npm run build"
  lint: "npm run lint"

paths:
  src: "src/"
  tests: "tests/"

conventions:
  - "Use TypeScript strict mode"
  - "Write tests for new features"
```

Now prompts automatically include your project's commands:

```bash
# Claude sees your test command without you specifying it
cplus verify --roles verifier
```

Auto-detects `.cplus.yml`, `package.json`, or `Makefile`. Use `cplus project init` to create a template.

## Composition Flow

When you run `cplus develop notes.md "focus on API"`, it composes:

```markdown
[Action: develop.md content]

### Project Context
**Commands**: test: `npm test`, build: `npm run build`
**Conventions**: Use TypeScript strict mode

### Additional Instructions
#### file: notes.md
[notes.md content]
#### text
focus on API
```

With `--roles architect`, it adds:

```markdown
### Roles
#### architect
[Role: architect.md content]
```

This gets piped to `claude`.

## Creating Custom Prompts

Use the `add` action to create new actions or roles interactively:

```bash
cplus add
```

This guides you through structured Q&A, generates a complete prompt following canonical schemas and Claude Code best practices, validates it, then saves it to the right location.

Or edit prompts directly:

```bash
cd ~/.config/cplus/prompts/
vim actions/my-action.md
vim roles/my-role.md
```

Or use the project symlink:

```bash
cd /path/to/cplus/prompts-installed/
vim actions/my-action.md
./sync-prompts.sh  # Sync changes
```

## Advanced

### Fuzzy Matching

```bash
cplus spec     # matches actions/spec.md
cplus dev      # matches actions/develop.md
--roles arch   # matches roles/architect.md (when roles are used)
```

### Dry Run

Preview without sending to Claude:

```bash
cplus develop --dry-run
```

### Role Injection

By default, roles are NOT injected. Use `--roles` to opt-in:

```bash
cplus develop                    # No roles
cplus develop --roles architect  # With architect role
```

## Maintenance

```bash
./sync-prompts.sh       # Sync prompts to installed location
./uninstall.sh          # Remove cplus
```

## Configuration

Prompts location: `~/.config/cplus/prompts/`

The `cplus` command looks for prompts in two places (in order):
1. Relative to the Python package (development/repo mode)
2. `~/.config/cplus/prompts/` (installed mode)

Override prompts location with `install.sh`:
```bash
export CPLUS_HOME="$HOME/.local/share/cplus"
./install.sh
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE)

## Credits

Built for [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli) by Anthropic.

ECC integration powered by [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa.
