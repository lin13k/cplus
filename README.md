# cplus

Prompt composition tool for [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli). Build complex prompts from reusable actions and roles.

## Features

- 🧩 **Composable prompts** - Build from reusable actions and roles
- 🎯 **Project context** - Auto-inject project commands from `.cplus.yml`, `package.json`, or `Makefile`
- ⚡ **Fuzzy matching** - Quick access without typing full names
- 📎 **Flexible context** - Attach files and text as needed
- 🔍 **Interactive selection** - fzf integration when you need it

## Quick Start

```bash
git clone https://github.com/lin13k/cplus.git
cd cplus
./install.sh

# Interactive mode
cplus

# Direct usage
cplus plan --roles architect
cplus implement --roles implementer tasks/task.md "focus on tests"
```

## Installation

**Prerequisites**: zsh, [Claude CLI](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/cli), fzf (`brew install fzf`)

```bash
./install.sh
```

Installs to `~/.config/cplus/` and creates `~/.local/bin/cplus` command.

## Usage

### Basic Commands

```bash
cplus [action] --roles [roles] [extras...]

# Examples
cplus plan --roles architect              # Use plan action with architect role
cplus implement --roles impl tasks/1.md   # Add file as context
cplus review --roles reviewer "check security"  # Add text context
cplus pick                                 # Interactive selection
cplus ls                                   # List available prompts
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
├── actions/          # What to do (plan, implement, review, etc.)
└── roles/            # How to behave (architect, implementer, etc.)
```

Actions define the task, roles define behavior. Compose them as needed:

```bash
cplus plan --roles architect              # Planning with architect mindset
cplus implement --roles implementer       # Implementing with focus on quality
cplus review --roles reviewer,architect   # Review with multiple perspectives
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

When you run `cplus plan --roles architect notes.md "focus on API"`, it composes:

```markdown
[Action: plan.md content]

### Roles
#### architect
[Role: architect.md content]

### Project Context
**Commands**: test: `npm test`, build: `npm run build`
**Conventions**: Use TypeScript strict mode

### Additional Instructions
#### file: notes.md
[notes.md content]
#### text
focus on API
```

This gets piped to `claude`.

## Creating Custom Prompts

Edit prompts directly:

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
cplus plan     # matches actions/plan.md
cplus impl     # matches actions/implement.md
--roles arch   # matches roles/architect.md
```

### Dry Run

Preview without sending to Claude:

```bash
cplus plan --roles architect --dry-run
```

### Skip Roles

```bash
cplus my-action --no-roles
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
