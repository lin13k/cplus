#!/usr/bin/env bash
# Cleanup a git worktree for a develop-v3 task.
# Usage: cleanup-worktree.sh <task-id>
#
# Removes the worktree and prunes references. Does NOT delete the task branch.

set -euo pipefail

TASK_ID="${1:?Usage: cleanup-worktree.sh <task-id>}"

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
WORKTREE_PATH="$(dirname "$PROJECT_ROOT")/${PROJECT_NAME}-${TASK_ID}"
TASK_DIR="$PROJECT_ROOT/.cplus/tasks/$TASK_ID"
STATE_FILE="$TASK_DIR/state.md"

# --- Remove worktree ---

if [ -d "$WORKTREE_PATH" ]; then
    # Check for uncommitted changes
    if [ -n "$(git -C "$WORKTREE_PATH" status --porcelain)" ]; then
        echo "Error: worktree has uncommitted changes:" >&2
        git -C "$WORKTREE_PATH" status --short >&2
        echo "" >&2
        echo "Commit or discard changes before cleanup." >&2
        exit 1
    fi

    echo "Removing worktree: $WORKTREE_PATH"
    git worktree remove "$WORKTREE_PATH"
else
    echo "Worktree already removed: $WORKTREE_PATH"
fi

# --- Prune stale references ---

git worktree prune
echo "Pruned stale worktree references"

# --- Update state.md ---

if [ -f "$STATE_FILE" ]; then
    # Remove existing Environment section and rewrite
    sed -i '' '/^## Environment$/,/^## /{ /^## Environment$/d; /^## /!d; }' "$STATE_FILE" 2>/dev/null || true

    cat >> "$STATE_FILE" << EOF

**Phase**: CLEANUP complete
**Status**: Done

## Environment
- Worktree: removed
- Branch: \`task/$TASK_ID\` (kept for reference)
EOF
fi

echo ""
echo "Cleanup complete:"
echo "  Worktree: removed"
echo "  Branch:   task/$TASK_ID (kept)"
