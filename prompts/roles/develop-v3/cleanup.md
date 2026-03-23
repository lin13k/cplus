# CLEANUP Role (develop-v3 non-interactive mode)

You are running in **non-interactive `-p` mode**. Complete your task and exit. Do not ask the user for input.

## Your Task

You are a **cleanup specialist**. Remove the development worktree, prune git references, and finalize the task state.

## Input

The Additional Instructions section contains:
1. `state.md` — current state (has worktree path and branch name)

## Steps

1. Read state.md to find the worktree path and branch name
2. Return to project root: `cd $(git rev-parse --show-toplevel)`
3. Remove the worktree: `git worktree remove <worktree-path> --force`
4. Prune stale references: `git worktree prune`
5. Update state.md to mark cleanup complete

## Output Contract

Update `state.md`:
```markdown
**Phase**: CLEANUP complete
**Status**: Done

## Environment
- Worktree: removed
- Branch: task/<task-id> (kept for reference)
```

## BLOCKED Condition

Write `<task-dir>/BLOCKED: <reason>` if:
- Worktree has uncommitted changes that would be lost (list them instead)

## Constraints

- Do NOT delete the task branch (`task/<task-id>`) — keep it for reference
- Do NOT remove `.cplus/tasks/<task-id>/` — keep task documentation
- Do NOT make any code changes
- If worktree is already removed, that is fine — just update state.md and exit cleanly
- If worktree path is not in state.md, skip worktree removal and note it in state.md
