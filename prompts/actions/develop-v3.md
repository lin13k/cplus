# develop-v3: Multi-Session Automated Pipeline

Run a fully automated, shell-orchestrated development pipeline where each phase executes as a fresh `claude -p` subprocess. Context never accumulates across phases. Git commits after every phase and checkpoint enable time-travel recovery.

## Usage

```bash
cplus develop-v3 <spec-file>                    # Run all phases (auto-resumes if progress exists)
cplus develop-v3 <spec-file> --from <phase>     # Resume from a specific phase
cplus develop-v3 <spec-file> --redo             # Discard existing progress and start fresh
```

## Pipeline

```
SETUP → ARCHITECT → IMPLEMENT (per checkpoint) → VERIFY → REVIEW → CLEANUP
```

Each phase is a separate `claude -p` subprocess reading context from files in `.cplus/tasks/<task-id>/`.

## --from Values

```
setup | architect | implement | checkpoint-N | verify | review | cleanup
```

Use `--from` after a `git reset --hard <phase-commit>` to re-run from a specific point.

## Git Commit Convention

Each phase produces a git commit:
```
cplus(setup): <task-id>
cplus(architect): <task-id>
cplus(checkpoint-1): <task-id>
cplus(checkpoint-2): <task-id>
cplus(verify): <task-id>
cplus(review): <task-id>
cplus(cleanup): <task-id>
```

## Role Prompts

Phase roles are in `prompts/roles/develop-v3/`. Each is designed for non-interactive `-p` mode:
reads context from files, writes outputs to files, writes `BLOCKED: <reason>` on failure.

## Differences from develop-v2

| | develop-v2 | develop-v3 |
|---|---|---|
| Session model | Single session with /compact | Fresh subprocess per phase |
| Context isolation | /compact at boundaries | Complete process isolation |
| Recovery | Re-run from start | git reset + --from |
| Interactivity | User approves each phase | Fully automated |
