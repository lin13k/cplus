# cplus

**cplus** (claude-plus) is a prompt composition tool for the [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli). Build complex, composable prompts from reusable action and role files, then pipe them directly to Claude.

## Why cplus?

Working with Claude CLI is powerful, but managing complex prompts becomes unwieldy:
- ❌ Long prompts are hard to maintain
- ❌ Copy-pasting role definitions is error-prone
- ❌ Reusing common patterns requires manual composition
- ❌ Context switching between files is tedious

**cplus solves this** by letting you:
- ✅ Break prompts into reusable **actions** and **roles**
- ✅ Compose prompts on-the-fly with fuzzy matching
- ✅ Mix and match roles for different tasks
- ✅ Attach files and text as additional context
- ✅ Auto-inject **project-specific commands** and conventions
- ✅ Use interactive selection when you need it
- ✅ Keep your prompts organized and maintainable

## Quick Start

```bash
# Install
git clone https://github.com/yourusername/cplus.git
cd cplus
./install.sh

# Interactive mode (pick action + roles)
cplus

# Use specific action with roles
cplus plan --roles architect,reviewer

# Add files and text as context
cplus implement --roles implementer tasks/123/task.md "focus on error handling"

# List available prompts
cplus ls
```

## Installation

### Prerequisites

- **zsh** (macOS default shell)
- **[Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli)** installed and in your PATH
- **fzf** (for interactive selection): `brew install fzf`
- **rsync** (usually pre-installed on macOS/Linux)

### Install

```bash
git clone https://github.com/yourusername/cplus.git
cd cplus
./install.sh
```

This will:
1. Copy cplus to `~/.config/cplus/`
2. Install prompts to `~/.config/cplus/prompts/`
3. Create `~/.local/bin/cplus` wrapper
4. Create `prompts-installed/` symlink for editing

### Verify Installation

```bash
cplus help
cplus ls
```

## Usage

### Basic Syntax

```bash
cplus [operation] [prompt_selector] [options] [extras...]
```

### Operations

| Operation | Description |
|-----------|-------------|
| `run` (default) | Build prompt and pipe to Claude |
| `pick` | Force interactive action selection |
| `ls [actions\|roles]` | List available prompts |
| `role --roles ...` | Show resolved role files |
| `project [show\|init\|validate]` | Manage project configuration |
| `help` | Show help message |

### Examples

#### Interactive Mode
```bash
# Pick action and roles interactively
cplus
```

#### Direct Action Selection
```bash
# Use fuzzy matching for action names
cplus plan                        # matches "plan.md"
cplus impl                        # matches "implement.md"
cplus verify --roles verifier     # specific action + role
```

#### With Roles
```bash
# Single role
cplus plan --roles architect

# Multiple roles (comma-separated)
cplus implement --roles implementer,reviewer

# Multiple roles (repeated flag)
cplus review --roles reviewer --roles architect
```

#### With Additional Context
```bash
# Add text context
cplus plan --roles arch "focus on performance"

# Add file context
cplus implement --roles impl tasks/123/task.md

# Mix text and files
cplus review --roles reviewer src/main.ts "check error handling"
```

#### Using Files as Base Prompts
```bash
# Any file path can be the base prompt
cplus tasks/123/custom-prompt.md --roles arch,impl
```

#### Listing and Inspection
```bash
# List all prompts
cplus ls

# List actions only
cplus ls actions

# List roles only
cplus ls roles

# See which files roles resolve to
cplus role --roles arch,impl,review
```

#### Dry Run
```bash
# Preview composed prompt without sending to Claude
cplus plan --roles arch --dry-run
```

## Prompt Structure

cplus organizes prompts into two categories:

```
prompts/
├── actions/          # Base prompts (what to do)
│   ├── plan.md
│   ├── implement.md
│   ├── review.md
│   └── verify.md
└── roles/            # Role modifiers (how to behave)
    ├── architect.md
    ├── implementer.md
    ├── reviewer.md
    └── verifier.md
```

### Actions

**Actions** define the primary task. Examples:
- `plan.md` - Create implementation plan
- `implement.md` - Write code for a feature
- `review.md` - Review code changes
- `verify.md` - Run tests and verify implementation

### Roles

**Roles** define behavior and constraints. Examples:
- `architect.md` - Think about system design, scalability
- `implementer.md` - Focus on clean, maintainable code
- `reviewer.md` - Look for bugs, security issues, edge cases
- `verifier.md` - Run tests, validate acceptance criteria

### Composition

When you run:
```bash
cplus plan --roles architect notes/requirements.md "focus on performance"
```

cplus composes:
```markdown
[Contents of prompts/actions/plan.md]

### Roles
#### architect
[Contents of prompts/roles/architect.md]

### Additional Instructions
#### file: notes/requirements.md
[Contents of notes/requirements.md]

#### text
focus on performance
```

This composed prompt is piped directly to `claude`.

## Project Context

cplus automatically detects and injects project-specific commands, paths, and conventions into your prompts. This makes Claude aware of your project's structure and commands without you having to repeat them every time.

### How It Works

1. **Auto-Detection**: cplus looks for project markers in your current directory:
   - `.cplus.yml` (explicit config, highest priority)
   - `package.json` (Node.js projects)
   - `Makefile` (Make-based projects)
   - `go.mod`, `Cargo.toml`, etc.

2. **Auto-Injection**: Project context is automatically added to all prompts between roles and extras:
   ```markdown
   [Base Prompt]

   ### Roles
   [Roles...]

   ### Project Context    **Project**: my-app
   **Commands**:
   - test: `npm test`
   - build: `npm run build`
   **Paths**:
   - src: `src/`
   - tests: `tests/`
   **Conventions**:
   - Use TypeScript strict mode

   ### Additional Instructions
   [Extras...]
   ```

### Creating a `.cplus.yml`

Create a `.cplus.yml` in your project root:

```yaml
# .cplus.yml
project:
  name: "my-app"
  description: "My awesome application"

commands:
  # Testing
  test: "npm test"
  test_file: "npm test -- <file>"

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
  config: "config/"

conventions:
  - "Use TypeScript strict mode"
  - "Follow Airbnb style guide"
  - "Write tests for all new features"
```

### Quick Commands

```bash
# Show detected project context
cplus project show

# Create .cplus.yml template
cplus project init

# Validate project config
cplus project validate
```

### Benefits

- ✅ Claude knows your test command automatically
- ✅ No need to repeat project conventions every time
- ✅ Consistent paths across all prompts
- ✅ Works with any project structure
- ✅ Falls back to package.json/Makefile if no .cplus.yml

### Example Usage

```bash
# Without project context, you'd have to say:
cplus verify --roles verifier "run pnpm test to verify"

# With project context, just say:
cplus verify --roles verifier
# Claude already knows the test command from .cplus.yml!
```

## Creating Custom Prompts

### Option 1: Edit Installed Prompts

```bash
# Edit directly (changes take effect immediately)
cd ~/.config/cplus/prompts/
vim actions/my-action.md
vim roles/my-role.md
```

### Option 2: Edit via Project Symlink

If you cloned the repo:
```bash
cd /path/to/cplus/prompts-installed/
vim actions/my-action.md
```

### Option 3: Sync from Project

If you edit prompts in the repo:
```bash
cd /path/to/cplus
vim prompts/actions/my-action.md
./sync-prompts.sh  # Sync to installed location
```

### Prompt Format

Prompts are plain markdown files. Use clear headers and examples:

**actions/my-action.md:**
```markdown
# Task: Implement Feature X

You are implementing a new feature. Follow these steps:

1. Read existing code
2. Plan the changes
3. Implement with tests
4. Verify it works

## Constraints
- Keep changes minimal
- Add tests for new functionality
- Update documentation
```

**roles/security-reviewer.md:**
```markdown
# Role: Security Reviewer

Review code with security-first mindset:

- Check for SQL injection, XSS, CSRF
- Validate input at boundaries
- Look for authentication/authorization issues
- Check for sensitive data exposure
- Review dependencies for known CVE
```

## Advanced Usage

### Fuzzy Matching

cplus uses fuzzy matching for action and role names:

```bash
cplus plan           # matches "plan.md"
cplus impl           # matches "implement.md"
cplus arch           # matches "architect.md" in roles
```

If multiple matches are found, you'll get an error with suggestions.

### Skip Roles

Some actions define their own roles and don't need additional ones:

```bash
cplus my-action --no-roles
```

### Interactive Selection

Force interactive selection even when specifying roles:

```bash
# Pick action interactively, then use specified roles
cplus pick --roles arch,impl
```

### Subdirectories

Organize roles in subdirectories:

```bash
prompts/roles/
├── architect.md
├── implementer.md
└── specialized/
    ├── ml-engineer.md
    └── devops.md
```

Access with path:
```bash
cplus plan --roles specialized/ml-engineer
```

## Maintenance

### Update Prompts

```bash
# If you edited prompts in the repo
cd /path/to/cplus
./sync-prompts.sh

# Preview changes first
./sync-prompts.sh --dry-run
```

### Uninstall

```bash
cd /path/to/cplus
./uninstall.sh
```

This removes:
- `~/.config/cplus/` directory
- `~/.local/bin/cplus` wrapper
- Project symlink `prompts-installed/`

### Reinstall

```bash
./uninstall.sh
./install.sh
```

## Configuration

### Custom Installation Location

```bash
export CPLUS_HOME="$HOME/.local/share/cplus"
./install.sh
```

### Add to PATH

The installer creates a wrapper at `~/.local/bin/cplus`. Ensure this is in your PATH:

```bash
# Add to ~/.zshrc if not already there
export PATH="$HOME/.local/bin:$PATH"
```

## Examples Gallery

### Multi-Agent Workflow

```bash
# Architect plans the feature
cplus plan --roles architect tasks/feature-x.md

# Implementer builds it
cplus implement --roles implementer tasks/feature-x/plan.md

# Verifier tests it
cplus verify --roles verifier "run all tests"

# Reviewer checks the code
cplus review --roles reviewer "focus on error handling"
```

### Documentation Task

```bash
cplus "Write API documentation" --roles technical-writer \
  src/api/*.ts "include examples and error codes"
```

### Bug Investigation

```bash
cplus investigate --roles debugger \
  tests/failing-test.ts \
  logs/error.log \
  "error happens intermittently"
```

### Refactoring

```bash
cplus refactor --roles architect,implementer \
  src/legacy-module.ts \
  "extract into smaller functions, add types"
```

## Troubleshooting

### "claude command not found"

Install Claude CLI:
```bash
# Follow instructions at:
# https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli
```

### "fzf is required"

Install fzf for interactive selection:
```bash
brew install fzf
```

### Prompts not syncing

```bash
# Check what would be synced
./sync-prompts.sh --dry-run

# Force sync
./sync-prompts.sh
```

### Wrong prompt selected

Use exact names or file paths:
```bash
# Exact match
cplus prompts/actions/plan.md

# Or use pick for interactive
cplus pick
```

## Philosophy

**cplus** follows these principles:

1. **Composition over monoliths** - Build complex prompts from simple, reusable pieces
2. **Convention over configuration** - Sensible defaults, minimal setup
3. **Fuzzy over exact** - Let the tool figure out what you mean
4. **Interactive when needed** - Fall back to selection when ambiguous
5. **Unix philosophy** - Do one thing well, compose with other tools

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `./install.sh` and verify all operations work
5. Submit a pull request

### Sharing Prompts

Have useful action or role prompts? Share them:
- Open an issue with your prompt
- Submit a PR to add it to the standard library
- Include description and use cases

## License

MIT License - see [LICENSE](LICENSE) file

## Credits

Created for use with [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli) by Anthropic.

## Related Tools

- [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli) - Official Claude command-line interface
- [Claude Desktop](https://claude.ai/download) - Claude desktop application

---

**Made with ❤️ for Claude CLI power users**
