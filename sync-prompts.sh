#!/usr/bin/env bash
# Sync prompts from project to installed cplus location

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"  # Script is in project root, not scripts/
CPLUS_HOME="${CPLUS_HOME:-$HOME/.config/cplus}"

SOURCE_PROMPTS="$PROJECT_ROOT/prompts"
TARGET_PROMPTS="$CPLUS_HOME/prompts"

# Parse options
DRY_RUN=false
VERBOSE=false

show_help() {
  cat << EOF
Usage: $(basename "$0") [options]

Sync prompts from project to installed cplus location.

OPTIONS:
  --dry-run, -n    Show what would be synced without actually syncing
  --verbose, -v    Show detailed sync output
  --help, -h       Show this help message

PATHS:
  Source: $SOURCE_PROMPTS
  Target: $TARGET_PROMPTS

EXAMPLES:
  # Sync prompts
  ./sync-prompts.sh

  # Preview what would be synced
  ./sync-prompts.sh --dry-run

  # Sync with detailed output
  ./sync-prompts.sh --verbose
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run|-n)
      DRY_RUN=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    *)
      echo "Error: Unknown option $1" >&2
      echo "Run with --help for usage information" >&2
      exit 1
      ;;
  esac
done

# Check that source prompts exist
if [[ ! -d "$SOURCE_PROMPTS" ]]; then
  echo "Error: Source prompts directory not found: $SOURCE_PROMPTS" >&2
  exit 1
fi

# Check that cplus is installed
if [[ ! -d "$CPLUS_HOME" ]]; then
  echo "Error: cplus not installed (directory not found: $CPLUS_HOME)" >&2
  echo "Run: ./install-cplus.sh" >&2
  exit 1
fi

# Create target prompts directory if it doesn't exist
if [[ ! -d "$TARGET_PROMPTS" ]]; then
  echo "⚠️  Target prompts directory doesn't exist: $TARGET_PROMPTS"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "   Would create: $TARGET_PROMPTS"
  else
    echo "   Creating: $TARGET_PROMPTS"
    mkdir -p "$TARGET_PROMPTS"
  fi
fi

echo "Syncing prompts..."
echo "  From: $SOURCE_PROMPTS"
echo "  To:   $TARGET_PROMPTS"
echo ""

# Build rsync options
RSYNC_OPTS="-av --delete"
if [[ "$DRY_RUN" == "true" ]]; then
  RSYNC_OPTS="$RSYNC_OPTS --dry-run"
  echo "DRY RUN MODE (no changes will be made)"
  echo ""
fi

if [[ "$VERBOSE" == "false" && "$DRY_RUN" == "false" ]]; then
  # Less verbose output for normal mode
  RSYNC_OPTS="-a --delete"
fi

# Check if rsync is available
if command -v rsync &> /dev/null; then
  # Use rsync for efficient sync
  if [[ "$VERBOSE" == "true" || "$DRY_RUN" == "true" ]]; then
    rsync $RSYNC_OPTS "$SOURCE_PROMPTS/" "$TARGET_PROMPTS/"
  else
    # Quiet mode for normal sync
    rsync $RSYNC_OPTS "$SOURCE_PROMPTS/" "$TARGET_PROMPTS/"
    echo "✓ Synced prompts"
  fi
else
  # Fallback to cp if rsync not available
  echo "⚠️  rsync not found, using cp (less efficient)"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "Would copy: $SOURCE_PROMPTS/* → $TARGET_PROMPTS/"
    find "$SOURCE_PROMPTS" -type f
  else
    cp -r "$SOURCE_PROMPTS/"* "$TARGET_PROMPTS/"
    echo "✓ Copied all files"
  fi
fi

if [[ "$DRY_RUN" == "false" ]]; then
  echo ""
  echo "✓ Prompts synced successfully!"
  echo ""
  echo "Changes are now available to the cplus command."
  echo ""
  echo "Tip: You can also edit prompts directly at:"
  echo "  $TARGET_PROMPTS/"
  echo "Or use the project symlink:"
  echo "  $PROJECT_ROOT/prompts-installed/"
else
  echo ""
  echo "Dry run complete. No changes were made."
fi
