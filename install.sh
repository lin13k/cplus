#!/usr/bin/env bash
# Install script for cplus - creates standalone installation with project symlink

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Installation locations
CPLUS_HOME="${CPLUS_HOME:-$HOME/.config/cplus}"
BIN_DIR="${HOME}/.local/bin"
CPLUS_BIN="$BIN_DIR/cplus"
PROJECT_PROMPTS_LINK="$PROJECT_ROOT/prompts-installed"

echo "Installing cplus..."
echo "Installation directory: $CPLUS_HOME"
echo ""

# Create directories
mkdir -p "$CPLUS_HOME"
mkdir -p "$BIN_DIR"

# Copy script
echo "Copying script..."
cp "$SCRIPT_DIR/cplus.zsh" "$CPLUS_HOME/cplus.zsh"
chmod +x "$CPLUS_HOME/cplus.zsh"

# Handle prompts directory
if [ -d "$CPLUS_HOME/prompts" ]; then
    echo "⚠️  Prompts already exist at $CPLUS_HOME/prompts"
    echo "   Keeping existing prompts (not overwriting)"
else
    echo "Copying prompts..."
    cp -r "$PROJECT_ROOT/prompts" "$CPLUS_HOME/"
fi

# Create symlink in project for IDE editing
if [ -L "$PROJECT_PROMPTS_LINK" ]; then
    echo "Symlink already exists: $PROJECT_PROMPTS_LINK"
elif [ -e "$PROJECT_PROMPTS_LINK" ]; then
    echo "⚠️  $PROJECT_PROMPTS_LINK exists but is not a symlink"
    echo "   Please move/remove it manually and reinstall"
else
    echo "Creating symlink for IDE editing..."
    ln -s "$CPLUS_HOME/prompts" "$PROJECT_PROMPTS_LINK"
    echo "✓ Created: $PROJECT_PROMPTS_LINK -> $CPLUS_HOME/prompts"
fi

# Create wrapper script in bin directory
echo "Creating wrapper script..."
cat > "$CPLUS_BIN" << 'EOF'
#!/usr/bin/env zsh
# cplus wrapper - calls the actual script from ~/.config/cplus
exec "$HOME/.config/cplus/cplus.zsh" "$@"
EOF
chmod +x "$CPLUS_BIN"

echo ""
echo "✓ Installed to: $CPLUS_HOME"
echo "✓ Created command: $CPLUS_BIN"
echo "✓ Created symlink: $PROJECT_PROMPTS_LINK"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "⚠️  $BIN_DIR is not in your PATH"
    echo "Add this to your ~/.zshrc:"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
else
    echo "✓ $BIN_DIR is already in your PATH"
fi

# Check for fzf
if ! command -v fzf &> /dev/null; then
    echo ""
    echo "⚠️  fzf is not installed (required for interactive selection)"
    echo "Install with: brew install fzf"
    echo ""
else
    echo "✓ fzf is installed"
fi

# Check for claude
if ! command -v claude &> /dev/null; then
    echo ""
    echo "⚠️  claude CLI is not installed"
    echo "cplus will work but needs claude to send prompts"
    echo ""
else
    echo "✓ claude CLI is installed"
fi

echo ""
echo "Installation complete! 🎉"
echo ""
echo "Files installed to:"
echo "  $CPLUS_HOME/cplus.zsh              # Main script"
echo "  $CPLUS_HOME/prompts/               # Prompts (actual location)"
echo "  $CPLUS_BIN                         # Command wrapper"
echo "  $PROJECT_PROMPTS_LINK -> prompts/  # Symlink for IDE"
echo ""
echo "Usage:"
echo "  cplus help                         # Show help"
echo "  cplus ls                           # List available prompts"
echo "  cplus plan --roles arch            # Use plan action with architect role"
echo ""
echo "Editing prompts in your IDE:"
echo "  Edit files in: $PROJECT_PROMPTS_LINK/"
echo "  They're actually stored at: $CPLUS_HOME/prompts/"
echo "  Changes are immediately available to cplus command!"
echo ""
echo "Syncing prompts from project to installed location:"
echo "  If you edit prompts in the project's prompts/ folder:"
echo "    ./scripts/sync-prompts.sh              # Sync changes to installed location"
echo "    ./scripts/sync-prompts.sh --dry-run    # Preview what would be synced"
echo ""
echo "Note: You may need to restart your shell or run: source ~/.zshrc"
