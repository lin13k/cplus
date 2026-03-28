#!/usr/bin/env bash
# Setup a git worktree for a develop-v3 task.
# Usage: setup-worktree.sh <task-id> [--install-cmd <cmd>]
#
# Creates:
#   - Git worktree at ../<project>-<task-id> (sibling to project root)
#   - New branch: task/<task-id>
#   - Runs install command if provided
#   - Appends Environment section to state.md

set -euo pipefail

TASK_ID="${1:?Usage: setup-worktree.sh <task-id> [--install-cmd <cmd>]}"
shift

INSTALL_CMD=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --install-cmd)
            INSTALL_CMD="$2"
            shift 2
            ;;
        *)
            echo "Error: unknown option $1" >&2
            exit 1
            ;;
    esac
done

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
WORKTREE_PATH="$(dirname "$PROJECT_ROOT")/${PROJECT_NAME}-${TASK_ID}"
BRANCH="task/${TASK_ID}"
TASK_DIR="$PROJECT_ROOT/.cplus/tasks/$TASK_ID"
STATE_FILE="$TASK_DIR/state.md"

# --- Create worktree + branch ---

if [ -d "$WORKTREE_PATH" ]; then
    echo "Worktree already exists: $WORKTREE_PATH"
    # Verify it's on the right branch
    CURRENT_BRANCH="$(git -C "$WORKTREE_PATH" rev-parse --abbrev-ref HEAD)"
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        echo "Error: worktree exists but is on branch '$CURRENT_BRANCH', expected '$BRANCH'" >&2
        exit 1
    fi
    echo "Reusing existing worktree (branch: $BRANCH)"
else
    echo "Creating worktree: $WORKTREE_PATH (branch: $BRANCH)"
    git worktree add "$WORKTREE_PATH" -b "$BRANCH"
fi

# --- Install dependencies ---

INSTALL_STATUS="skipped"
if [ -n "$INSTALL_CMD" ]; then
    echo "Installing dependencies: $INSTALL_CMD"
    if (cd "$WORKTREE_PATH" && eval "$INSTALL_CMD"); then
        INSTALL_STATUS="verified"
    else
        echo "Error: install command failed" >&2
        exit 1
    fi
else
    echo "No install command provided, skipping dependency installation"
fi

# --- Verify clean state ---

if [ -n "$(git -C "$WORKTREE_PATH" status --porcelain)" ]; then
    echo "Warning: worktree has uncommitted changes after install"
fi

# --- Update state.md ---

mkdir -p "$TASK_DIR"
if [ -f "$STATE_FILE" ]; then
    # Remove existing Environment section if present (for re-runs)
    sed -i '' '/^## Environment$/,/^## /{ /^## Environment$/d; /^## /!d; }' "$STATE_FILE" 2>/dev/null || true
fi

cat >> "$STATE_FILE" << EOF

## Environment
- Worktree: \`$WORKTREE_PATH\`
- Branch: \`$BRANCH\`
- Install: $INSTALL_STATUS
EOF

echo ""
echo "Setup complete:"
echo "  Worktree: $WORKTREE_PATH"
echo "  Branch:   $BRANCH"
echo "  Install:  $INSTALL_STATUS"
