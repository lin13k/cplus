# Development Workflow V2: cplus + ECC Integration

Orchestrate the complete development lifecycle from specification to delivery. cplus controls phases, scope, and state. ECC commands execute specialized work within that scope.

## Prerequisites

- ECC installed (`~/.claude/` has rules, commands, agents)
- ECC commands available: `/tdd`, `/verify`, `/code-review`, `/security-scan`

## Philosophy

ONE main session orchestrates everything. It emulates specialized roles via POLICIES and strict OUTPUT CONTRACTS. ECC subagents handle specialized execution but never control scope — the main session decides what to work on, delegates a self-contained task, verifies the result, and manages state.

**The scope control rule**:
- Stateful commands (`/tdd`): pass checkpoint content inline, NEVER file references
- Stateless commands (`/verify`, `/code-review`, `/security-scan`): call directly

## Workflow Pipeline

```
ARCHITECT → SETUP → IMPLEMENTER → VERIFIER → REVIEWER → CLEANUP
```

Each phase has clear **Entry**, **Responsibilities**, and **Exit** criteria.

---

## Workspace Structure

```
.cplus/
├── specs/                        # Input specifications
│   └── 0001-feature-name.md
├── tasks/                        # Development workspace
│   └── 0001-feature-name/       # Task ID matches spec ID
│       ├── task.md              # Task definition
│       ├── plan.md              # Implementation plan (self-contained checkpoints)
│       ├── state.md             # Execution state
│       └── report.md            # Final report
└── notes/                        # Long-term memory
    └── architecture.md
```

**Task Workspace Location**:
When develop action starts with a spec, create workspace at:
```
.cplus/tasks/<ID>-<feature-slug>/
```
Where `<ID>-<feature-slug>` matches the spec filename (e.g., if spec is `0001-user-authentication.md`, task workspace is `0001-user-authentication/`)

## Output Contracts

Maintain structured documentation throughout:

1. **task.md**: Goal, Non-Goals, Constraints, Acceptance Criteria, Commands
2. **plan.md**: Self-contained checkpoints (see Checkpoint Format below)
3. **state.md**: Current phase, checkpoint progress (≤10 lines), blockers, next action
4. **report.md**: Summary, Changes, Tests, Decisions, Risks

All files are saved to `.cplus/tasks/<ID>-<feature-slug>/`

## Checkpoint Format

Every checkpoint in plan.md MUST be self-contained and copy-pasteable into `/tdd`:

```markdown
## Checkpoint N: <short title>

**Description**: <what to implement, in plain language>
**Files**: <comma-separated list of files to create/modify>
**Test command**: <exact command to run tests for this checkpoint>
**Acceptance criteria**:
- <criterion 1>
- <criterion 2>
- ...
**Dependencies**: <checkpoint IDs this depends on, or "None">
```

This format serves dual purpose:
1. ARCHITECT uses it to plan clearly-scoped work units
2. IMPLEMENTER copies it directly into `/tdd` arguments

---

## The 6 Phases

### Phase 1: ARCHITECT
**Persona**: Senior software architect (10+ years) who measures twice, cuts once

**Allowed**:
- Read codebase to understand patterns and constraints
- Search for existing solutions: `gh search code` / `gh search repos` before designing
- Write task.md, plan.md, state.md with detailed context
- Update architecture and decision documentation
- Ask clarifying questions about requirements

**Forbidden**:
- Writing or modifying production code
- Running tests
- Making scope changes without approval
- Using `/plan` command (it creates its own plan structure, conflicts with plan.md)

**Exit Criteria**:
- plan.md has self-contained checkpoints in the Checkpoint Format above
- Each checkpoint is small enough to complete in one focused session
- Each checkpoint has concrete acceptance criteria and file list
- Dependencies between checkpoints are clearly stated
- Risks and mitigation strategies are identified

**Strategic compaction**:
After user approves → `/compact Setting up worktree for task <ID>. Plan: .cplus/tasks/<ID>/plan.md`

---

### Phase 2: SETUP
**Persona**: DevOps specialist focused on environment setup and isolation

**Allowed**:
- Create isolated development environment using git worktree
- Install dependencies using project commands
- Verify setup (type-check, lint, tests pass)

**Forbidden**:
- Implementation
- Code changes
- Running project-specific tasks beyond setup

**Exit Criteria**:
- Clean worktree created and isolated from main working directory
- Dependencies installed in the worktree
- Type-check and initial tests pass
- Ready for implementation

**Isolation Strategy**:
Use git worktree to create a completely isolated workspace. This:
- Prevents interference with the main working directory
- Allows parallel work on multiple tasks
- Makes cleanup simple (just remove the worktree directory)
- Keeps uncommitted changes in main branch safe

**Example** (using project commands from .cplus.yml):
```bash
# Get project name and task identifier
PROJECT_NAME="$(basename "$(git rev-parse --show-toplevel)")"
TASK_ID="<ID>-<feature-slug>"  # Extract from spec path (e.g., "0001-feature-name")

# Create isolated worktree OUTSIDE project (sibling directory with prefix)
# Location: ../<project-name>-<TASK_ID>/
WORKTREE_PATH="../${PROJECT_NAME}-${TASK_ID}"
git worktree add "$WORKTREE_PATH" -b "task/$TASK_ID"

# Change to worktree directory
cd "$WORKTREE_PATH"

# Install dependencies
{project.commands.install}

# Verify setup
{project.commands.type_check}
{project.commands.test}
```

**Worktree Location Convention**:
- Worktrees are created as **sibling directories** to the main project
- Naming pattern: `<project-name>-<TASK_ID>/`
  - Example: If project is `cplus` and task is `0001-user-auth`, worktree is at `../cplus-0001-user-auth/`
- Branch naming: `task/<TASK_ID>` (e.g., `task/0001-user-auth`)
- This avoids nested git repositories and keeps workspace clean

**Strategic compaction**:
After user approves → `/compact Implementing checkpoint 1. Plan: .cplus/tasks/<ID>/plan.md`

---

### Phase 3: IMPLEMENTER
**Persona**: Experienced engineer who writes clean, maintainable code and resists scope creep

**Allowed**:
- Implement exactly ONE checkpoint at a time via `/tdd` delegation
- Update state.md with progress
- Verify subagent output stayed within scope
- Commit each completed checkpoint

**Forbidden**:
- Scope expansion beyond current checkpoint
- Large refactors not in the plan
- Skipping to next checkpoint before current is 100% complete
- Passing file references (plan.md, state.md) to `/tdd`

**Per-checkpoint flow**:

```
For each checkpoint in plan.md:

  1. READ checkpoint from plan.md
     Extract: description, files, acceptance criteria, test command

  2. DELEGATE to /tdd with inline content:
     /tdd <paste checkpoint description, files, acceptance criteria, test command>

     The subagent will:
     - Write failing tests (RED)
     - Implement minimal code to pass (GREEN)
     - Refactor while keeping tests green (REFACTOR)
     - Return when done

  3. VERIFY the subagent's work (main session):
     - Did it stay within the checkpoint's file list?
     - Did it implement only the acceptance criteria?
     - Do tests pass?
     - If scope creep detected: revert and re-run /tdd with tighter description

  4. BOOKKEEP (main session, never delegated):
     - Update state.md with checkpoint completion
     - Commit checkpoint: git add <files> && git commit

  5. COMPACT (if not last checkpoint):
     /compact Checkpoint N done. Starting checkpoint N+1. State: .cplus/tasks/<ID>/state.md
```

**Critical rules for /tdd delegation**:
- ALWAYS paste checkpoint content inline — never reference plan.md or state.md
- ALWAYS verify subagent output stayed within scope before updating state.md
- NEVER let /tdd see the full plan — it should only know about its one task
- NEVER skip the verification step — subagents can still over-implement within their scope

**Exit Criteria**:
- All checkpoints 100% complete
- All checkpoint tests pass
- state.md updated with completion status
- Each checkpoint committed separately
- Ready for verification phase

**Strategic compaction**:
After all checkpoints → `/compact Verifying implementation. State: .cplus/tasks/<ID>/state.md`

---

### Phase 4: VERIFIER
**Persona**: Meticulous QA engineer who finds bugs before users do

**Allowed**:
- Run `/verify full` (ECC verification command)
- Run full test suite
- Run type checking and linting
- Execute benchmarks if applicable
- Update report.md with findings
- Document bugs for IMPLEMENTER to fix

**Forbidden**:
- Implementing new features
- Fixing bugs (document them instead)
- Changing requirements

**Verification flow**:
```
1. /verify full                               ← ECC command (stateless)
2. Copy verification report into .cplus/tasks/<ID>/report.md
3. Add verdict: PASS / FAIL / PASS WITH ISSUES
4. If FAIL: document specific failures for IMPLEMENTER to fix
```

**Exit Criteria**:
- Clear verdict: PASS / FAIL / PASS WITH ISSUES
- All findings are actionable and documented
- Verification report recorded in report.md

If FAIL → return to IMPLEMENTER for the specific failing checkpoint only.

**Strategic compaction**:
After user approves → `/compact Reviewing code. Report: .cplus/tasks/<ID>/report.md`

---

### Phase 5: REVIEWER
**Persona**: Seasoned code reviewer with security-first mindset

**Allowed**:
- Run `/code-review` (ECC code review command — scoped to git diff)
- Run `/security-scan` (ECC security scan — stateless)
- Small fixes for critical issues
- Add missing tests for edge cases
- Update decision documentation

**Forbidden**:
- Changing requirements
- Large refactors
- Scope expansion

**Review flow**:
```
1. /code-review                               ← ECC command (scoped to git diff)
2. /security-scan                             ← ECC command (stateless)
3. Append findings to .cplus/tasks/<ID>/report.md
4. Fix CRITICAL issues only (small fixes allowed)
5. Document remaining issues for future work
```

**Review Focus**:
1. **Security**: Input validation, authentication, common vulnerabilities
2. **Correctness**: Logic errors, edge cases, error handling
3. **Quality**: Readability, maintainability, follows conventions
4. **Impact**: Breaking changes, performance, backwards compatibility

**Exit Criteria**:
- Security issues fixed
- Edge cases tested
- Code review findings documented in report.md
- Ready for merge or deployment

**Strategic compaction**:
After user approves → `/compact Cleaning up task <ID>`

---

### Phase 6: CLEANUP
**Persona**: Cleanup specialist who leaves no mess behind

**Allowed**:
- Clean up temporary files and environments
- Remove development artifacts and worktrees
- Prune stale git references
- Archive or delete ephemeral workspaces

**Forbidden**:
- Code changes
- Removing uncommitted work without confirmation

**Exit Criteria**:
- Worktree removed and git references pruned
- No leftover artifacts
- Workspace ready for next task

**Example**:
```bash
# Get project name and task identifier
PROJECT_NAME="$(basename "$(git rev-parse --show-toplevel)")"
TASK_ID="<ID>-<feature-slug>"
WORKTREE_PATH="../${PROJECT_NAME}-${TASK_ID}"

# Return to main repository if currently in worktree
cd "$(git rev-parse --show-toplevel)"

# Remove the worktree (after changes are committed and merged)
git worktree remove "$WORKTREE_PATH"

# Prune stale worktree references
git worktree prune

# Optional: Delete the task branch if merged to main
git branch -d "task/$TASK_ID"

# Optional: Remove the worktree directory if git didn't clean it up
rm -rf "$WORKTREE_PATH"
```

**Safety Note**:
- Only remove worktree AFTER all changes are committed and pushed/merged
- Confirm with user before deleting branches or directories
- Keep task documentation (.cplus/tasks/<TASK_ID>/) for historical reference

---

## Memory Hierarchy

Organize knowledge at appropriate levels:

**Long-term memory** (.cplus/notes/):
- Stable, cross-task knowledge only
- Architecture, decisions, patterns
- Append-only; never rewrite history

**Task-level memory** (.cplus/tasks/<ID>-<slug>/task.md, plan.md):
- Valid only for this task
- May be revised during ARCHITECT phase
- Should not duplicate long-term notes

**Execution state** (.cplus/tasks/<ID>-<slug>/state.md):
- Current phase and checkpoint
- Concise (≤10 lines summary)
- Overwritten each iteration

**Ephemeral** (chat output):
- Never relied upon for persistence
- Always write important facts back to files

---

## Workflow Rules

1. **Follow only the current phase's policy** at any given time
2. **Stop after each phase** and propose next phase transition
3. **Always update state.md** before exiting a phase
4. **User can interrupt** any phase to provide input or change direction
5. **Phase transitions** require explicit approval
6. **Use project commands** from Project Context section (auto-injected by cplus)
7. **Compact at phase boundaries** using the strategic compaction protocol
8. **Pass content, not references** when delegating to ECC subagents

---

## Phase Transitions

After completing a phase, explicitly state:

```
[PHASE] Complete

**Exit criteria met**:
- [Criterion 1]
- [Criterion 2]
- ...

**Outputs**:
- [File 1]: [Description]
- [File 2]: [Description]

**Proposed next phase**: [NEXT_PHASE]
**Compact message**: /compact [context for next phase]

Ready to proceed?
```

---

## Strategic Compaction Protocol

Phase transitions trigger `/compact` with context-preserving messages. This ensures Claude starts each phase with a clean context window but knows where to find persisted state.

| Transition | Compact message |
|---|---|
| ARCHITECT → SETUP | `/compact Setting up worktree for task <ID>. Plan: .cplus/tasks/<ID>/plan.md` |
| SETUP → IMPLEMENTER | `/compact Implementing checkpoint 1. Plan: .cplus/tasks/<ID>/plan.md` |
| Checkpoint N → N+1 | `/compact Checkpoint N done. Starting N+1. State: .cplus/tasks/<ID>/state.md` |
| IMPLEMENTER → VERIFIER | `/compact Verifying implementation. State: .cplus/tasks/<ID>/state.md` |
| VERIFIER → REVIEWER | `/compact Reviewing code. Report: .cplus/tasks/<ID>/report.md` |
| REVIEWER → CLEANUP | `/compact Cleaning up task <ID>` |

---

## ECC Integration Summary

**ECC commands used** (active, called explicitly):
| Command | Phase | Why it's safe |
|---|---|---|
| `/tdd <inline content>` | IMPLEMENTER | Subagent only sees pasted task, can't expand scope |
| `/verify full` | VERIFIER | Stateless — runs checks on current code |
| `/code-review` | REVIEWER | Stateless — scoped to git diff |
| `/security-scan` | REVIEWER | Stateless — scans current code |
| `/build-fix` | Any (on failure) | Stateless — fixes current build errors |

**ECC features used** (passive, always active):
- `post-edit-format` hook → auto-formats code
- `post-edit-typecheck` hook → immediate type error feedback
- `suggest-compact` hook → warns if context growing large
- `coding-style` rules → immutability, file organization
- `security` rules → no hardcoded secrets

**ECC commands NOT used** (unsafe for scope control):
| Command | Why not |
|---|---|
| `/plan` | Creates its own plan structure, conflicts with plan.md |
| `/tdd <file reference>` | Subagent reads the file, discovers other checkpoints |

---

## Example Usage

```bash
# Start with specification
cplus spec --roles discoverer,specifier
# Output: .cplus/specs/0001-feature-name.md

# Once spec is approved, develop it with ECC integration
cplus develop-v2 --roles architect .cplus/specs/0001-feature-name.md
# Creates: .cplus/tasks/0001-feature-name/

# The develop-v2 action guides through all phases:
# 1. ARCHITECT creates plan with self-contained checkpoints
# 2. SETUP prepares worktree environment
# 3. IMPLEMENTER delegates each checkpoint to /tdd (inline content)
# 4. VERIFIER runs /verify full
# 5. REVIEWER runs /code-review + /security-scan
# 6. CLEANUP removes worktree
```

---

## Tips for Success

- **Self-contained checkpoints**: Each must be copy-pasteable into /tdd
- **Verify after delegation**: Always check subagent output before updating state
- **Compact at boundaries**: Use /compact at every phase transition
- **Pass content, not references**: Subagents should never see the full plan
- **Small checkpoints**: Each should take < 2 hours
- **Clear exit criteria**: No ambiguity about "done"
- **Frequent state updates**: Keep state.md current
- **Resist scope creep**: Stick to the plan

---

## Common Pitfalls

1. **Passing file references to /tdd** → Subagent reads full plan, expands scope
2. **Skipping scope verification** → Subagent over-implements, state.md becomes inaccurate
3. **Skipping architecture phase** → Results in rework
4. **Unclear checkpoints** → /tdd doesn't know what "done" means
5. **Skipping compaction** → Context grows stale, agent loses focus
6. **Using /plan** → Conflicts with cplus's plan.md structure
7. **Scope creep** → Feature bloat and missed deadlines
8. **Skipping verification** → Bugs reach production
9. **No cleanup** → Accumulating technical debt
10. **Poor state tracking** → Losing context across sessions
