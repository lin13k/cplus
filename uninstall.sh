#!/usr/bin/env bash
# Uninstall script for cplus

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

CPLUS_HOME="${CPLUS_HOME:-$HOME/.config/cplus}"
CPLUS_BIN="$HOME/.local/bin/cplus"
PROJECT_PROMPTS_LINK="$PROJECT_ROOT/prompts-installed"

echo "Uninstalling cplus..."
echo ""

# Ask for confirmation before removing prompts
if [ -d "$CPLUS_HOME/prompts" ]; then
    echo "⚠️  This will delete your prompts at: $CPLUS_HOME/prompts"
    echo "   (including any custom prompts you've added)"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstall cancelled."
        exit 0
    fi
fi

# Remove installation directory
if [ -d "$CPLUS_HOME" ]; then
    echo "Removing $CPLUS_HOME"
    rm -rf "$CPLUS_HOME"
    echo "✓ Removed installation directory"
else
    echo "⚠️  $CPLUS_HOME not found (already uninstalled?)"
fi

# Remove bin wrapper
if [ -f "$CPLUS_BIN" ]; then
    echo "Removing $CPLUS_BIN"
    rm "$CPLUS_BIN"
    echo "✓ Removed command wrapper"
else
    echo "⚠️  $CPLUS_BIN not found (already uninstalled?)"
fi

# Remove project symlink
if [ -L "$PROJECT_PROMPTS_LINK" ]; then
    echo "Removing symlink $PROJECT_PROMPTS_LINK"
    rm "$PROJECT_PROMPTS_LINK"
    echo "✓ Removed project symlink"
elif [ -e "$PROJECT_PROMPTS_LINK" ]; then
    echo "⚠️  $PROJECT_PROMPTS_LINK exists but is not a symlink (skipping)"
fi

echo ""
echo "Uninstallation complete!"
echo ""
echo "Note: Original prompts still exist at:"
echo "  $PROJECT_ROOT/prompts/"
