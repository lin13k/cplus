#!/usr/bin/env bash
# Install script for cplus - creates standalone installation with project symlink
# Optionally installs ECC (Everything Claude Code) for develop-v2 integration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Installation locations
CPLUS_HOME="${CPLUS_HOME:-$HOME/.config/cplus}"
BIN_DIR="${HOME}/.local/bin"
CPLUS_BIN="$BIN_DIR/cplus"
PROJECT_PROMPTS_LINK="$PROJECT_ROOT/prompts-installed"
CLAUDE_DIR="$HOME/.claude"

# Parse flags
INSTALL_ECC=false
ECC_LANGS=""
for arg in "$@"; do
    case "$arg" in
        --with-ecc) INSTALL_ECC=true ;;
        --ecc-langs=*) ECC_LANGS="${arg#--ecc-langs=}" ;;
        --help|-h)
            echo "Usage: ./install.sh [--with-ecc] [--ecc-langs=typescript,python,golang]"
            echo ""
            echo "Options:"
            echo "  --with-ecc              Install ECC (Everything Claude Code) for develop-v2"
            echo "  --ecc-langs=lang1,lang2 Language-specific ECC rules (default: none)"
            echo ""
            echo "Examples:"
            echo "  ./install.sh                                    # cplus only"
            echo "  ./install.sh --with-ecc                         # cplus + ECC (common rules only)"
            echo "  ./install.sh --with-ecc --ecc-langs=typescript  # cplus + ECC with TypeScript rules"
            exit 0
            ;;
    esac
done

echo "Installing cplus..."
echo "Installation directory: $CPLUS_HOME"
echo ""

# Create directories
mkdir -p "$CPLUS_HOME"
mkdir -p "$BIN_DIR"

# Install Python package
echo "Installing Python package..."
if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
    pip install "$PROJECT_ROOT" 2>&1 | tail -3
else
    echo "Error: pyproject.toml not found in $PROJECT_ROOT" >&2
    exit 1
fi

# Handle prompts directory
if [ -d "$CPLUS_HOME/prompts" ]; then
    echo "Prompts already exist at $CPLUS_HOME/prompts"
    echo "   Keeping existing prompts (not overwriting)"
else
    echo "Copying prompts..."
    cp -r "$PROJECT_ROOT/prompts" "$CPLUS_HOME/"
fi

# Create symlink in project for IDE editing
if [ -L "$PROJECT_PROMPTS_LINK" ]; then
    echo "Symlink already exists: $PROJECT_PROMPTS_LINK"
elif [ -e "$PROJECT_PROMPTS_LINK" ]; then
    echo "$PROJECT_PROMPTS_LINK exists but is not a symlink"
    echo "   Please move/remove it manually and reinstall"
else
    echo "Creating symlink for IDE editing..."
    ln -s "$CPLUS_HOME/prompts" "$PROJECT_PROMPTS_LINK"
    echo "Created: $PROJECT_PROMPTS_LINK -> $CPLUS_HOME/prompts"
fi

echo ""
echo "[cplus] Installed Python package with 'cplus' entry point"
echo "[cplus] Prompts at: $CPLUS_HOME/prompts"
echo ""

# --- ECC Installation ---
if [ "$INSTALL_ECC" = true ]; then
    echo "--- Installing ECC (Everything Claude Code) ---"
    echo ""

    ECC_DIR="${ECC_DIR:-$HOME/projects/everything-claude-code}"

    if [ ! -d "$ECC_DIR" ]; then
        echo "Cloning ECC repository..."
        git clone https://github.com/affaan-m/everything-claude-code.git "$ECC_DIR"
    else
        echo "ECC repository found at $ECC_DIR"
    fi

    # Install ECC rules (common + language-specific)
    echo "Installing ECC rules..."
    mkdir -p "$CLAUDE_DIR/rules/common"
    cp -r "$ECC_DIR/rules/common/." "$CLAUDE_DIR/rules/common/"
    echo "[ecc] Installed common rules -> $CLAUDE_DIR/rules/common/"

    if [ -n "$ECC_LANGS" ]; then
        IFS=',' read -ra LANGS <<< "$ECC_LANGS"
        for lang in "${LANGS[@]}"; do
            lang=$(echo "$lang" | tr -d ' ')
            if [ -d "$ECC_DIR/rules/$lang" ]; then
                mkdir -p "$CLAUDE_DIR/rules/$lang"
                cp -r "$ECC_DIR/rules/$lang/." "$CLAUDE_DIR/rules/$lang/"
                echo "[ecc] Installed $lang rules -> $CLAUDE_DIR/rules/$lang/"
            else
                echo "[ecc] Warning: rules/$lang/ does not exist, skipping"
            fi
        done
    fi

    # Install ECC commands (used by develop-v2: /tdd, /verify, /code-review, /security-scan)
    echo "Installing ECC commands..."
    mkdir -p "$CLAUDE_DIR/commands"
    cp -r "$ECC_DIR/commands/." "$CLAUDE_DIR/commands/"
    echo "[ecc] Installed commands -> $CLAUDE_DIR/commands/"

    # Install ECC agents (used by commands: tdd-guide, code-reviewer, etc.)
    echo "Installing ECC agents..."
    mkdir -p "$CLAUDE_DIR/agents"
    cp -r "$ECC_DIR/agents/." "$CLAUDE_DIR/agents/"
    echo "[ecc] Installed agents -> $CLAUDE_DIR/agents/"

    # Install ECC skills
    echo "Installing ECC skills..."
    mkdir -p "$CLAUDE_DIR/skills"
    cp -r "$ECC_DIR/skills/." "$CLAUDE_DIR/skills/"
    echo "[ecc] Installed skills -> $CLAUDE_DIR/skills/"

    # Install ECC hook scripts
    echo "Installing ECC hook scripts..."
    mkdir -p "$CLAUDE_DIR/scripts/hooks"
    cp -r "$ECC_DIR/scripts/hooks/." "$CLAUDE_DIR/scripts/hooks/"
    echo "[ecc] Installed hook scripts -> $CLAUDE_DIR/scripts/hooks/"

    # Install hooks.json (merge with existing if present)
    if [ -f "$CLAUDE_DIR/hooks.json" ]; then
        echo "[ecc] hooks.json already exists at $CLAUDE_DIR/hooks.json"
        echo "      ECC hooks saved to $CLAUDE_DIR/hooks.ecc.json for manual merge"
        cp "$ECC_DIR/hooks/hooks.json" "$CLAUDE_DIR/hooks.ecc.json"
    else
        cp "$ECC_DIR/hooks/hooks.json" "$CLAUDE_DIR/hooks.json"
        echo "[ecc] Installed hooks.json -> $CLAUDE_DIR/hooks.json"
    fi

    echo ""
    echo "[ecc] ECC installation complete"
    echo "[ecc] ECC source: $ECC_DIR"
    echo ""
fi

# --- Dependency checks ---
echo "--- Checking dependencies ---"

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "  python3: not installed (required)"
    echo "  Install with: brew install python"
else
    echo "  python3: ok ($(python3 --version 2>&1))"
fi

# Check for pip
if ! command -v pip &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "  pip: not installed (required)"
else
    echo "  pip: ok"
fi

# Check cplus entry point is in PATH
if ! command -v cplus &> /dev/null; then
    echo "  cplus: not found in PATH"
    echo "  You may need to add pip's script directory to your PATH"
    echo "  Try: pip show cplus | grep Location"
else
    echo "  cplus: ok"
fi

# Check for fzf
if ! command -v fzf &> /dev/null; then
    echo "  fzf: not installed (required for interactive selection)"
    echo "  Install with: brew install fzf"
else
    echo "  fzf: ok"
fi

# Check for claude
if ! command -v claude &> /dev/null; then
    echo "  claude: not installed (required to send prompts)"
else
    echo "  claude: ok"
fi

# Check for ECC if develop-v2 prompts exist
if [ -f "$CPLUS_HOME/prompts/actions/develop-v2.md" ] && [ "$INSTALL_ECC" = false ]; then
    if [ ! -d "$CLAUDE_DIR/commands" ] || [ ! -f "$CLAUDE_DIR/commands/tdd.md" ]; then
        echo ""
        echo "  Note: develop-v2 action requires ECC."
        echo "  Reinstall with: ./install.sh --with-ecc"
    fi
fi

echo ""
echo "--- Installation complete ---"
echo ""
echo "Usage:"
echo "  cplus help                         # Show help"
echo "  cplus ls                           # List available prompts"
echo "  cplus spec                         # Run spec action"
echo "  cplus develop                      # Run develop action (v1)"
if [ "$INSTALL_ECC" = true ]; then
    echo "  cplus develop-v2                   # Run develop action with ECC integration"
fi
echo "  cplus develop-v3 <spec>            # Automated multi-session pipeline"
echo ""
echo "Note: You may need to restart your shell or run: source ~/.zshrc"
