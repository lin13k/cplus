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

### Structured workflows — Claude focuses on one thing at a time

```bash
# 1. Spec out a feature through guided discovery
#    DISCOVERER → SPECIFIER → VALIDATOR → REFINER
cplus spec "SSO integration with Google and GitHub OAuth"

# 2. Develop it end-to-end with phased execution
#    ARCHITECT → SETUP → IMPLEMENTER → VERIFIER → REVIEWER → CLEANUP
#    Each phase has strict scope — can't write code during planning, can't skip tests
cplus develop .cplus/specs/0001-sso-integration.md

# 3. Or use develop-v2 with ECC (requires --with-ecc install)
#    Same phases, but IMPLEMENTER delegates to /tdd, VERIFIER runs /verify, etc.
cplus develop-v2 .cplus/specs/0001-sso-integration.md
```

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

**Prerequisites**: zsh, [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli), fzf (`brew install fzf`)

### cplus only

```bash
./install.sh
```

Installs to `~/.config/cplus/` and creates `~/.local/bin/cplus` command.

### cplus + ECC (recommended for develop-v2)

```bash
./install.sh --with-ecc
```

This additionally installs ECC's rules, commands, agents, skills, and hooks into `~/.claude/`. If you want language-specific rules:

```bash
./install.sh --with-ecc --ecc-langs=typescript,python,golang
```

ECC source is cloned to `~/projects/everything-claude-code/` (set `ECC_DIR` to override).

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

Default install location: `~/.config/cplus/`

Override with:
```bash
export CPLUS_HOME="$HOME/.local/share/cplus"
./install.sh
```

Ensure `~/.local/bin` is in your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE)

## Credits

Built for [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli) by Anthropic.

ECC integration powered by [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa.
