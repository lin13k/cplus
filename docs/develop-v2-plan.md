# DevelopV2: cplus + ECC Integration Plan

## Problem

cplus's `develop` action has strong **focus management** (phased execution, role boundaries, checkpoint discipline) but lacks the tooling ECC provides (code review agents, TDD guidance, security scanning, strategic compaction, auto-formatting hooks).

Currently these two systems don't talk to each other. DevelopV2 bridges them.

## The Core Tension: Who Controls Scope?

ECC's slash commands (`/tdd`, `/code-review`, `/plan`) invoke **subagents** — separate agent processes with their own system prompts. When cplus's IMPLEMENTER calls `/tdd`:

```
cplus develop prompt (loaded in main session)
  └── /tdd invokes tdd-guide subagent
       └── subagent has its OWN system prompt (tdd-guide.md + tdd-workflow skill)
       └── subagent does NOT see cplus's phase rules, role boundaries, or state.md
       └── subagent decides scope on its own
```

**The subagent doesn't know it should only implement checkpoint 3.** It'll implement whatever it thinks is right. cplus loses focus control.

### The solution: pass content, not references

```
/tdd Only implement checkpoint 3 from .cplus/tasks/0001/plan.md
```

This is dangerous — the subagent can read plan.md, see all checkpoints, and expand scope.

Instead, **copy the checkpoint content inline**:

```
/tdd Add JWT validation middleware.
     Input: request headers with Authorization bearer token.
     Output: 401 if invalid/expired, call next() if valid.
     Files: src/middleware/auth.ts, src/middleware/auth.test.ts
     Test command: npm test src/middleware/auth.test.ts
     Acceptance criteria:
     - Returns 401 for missing token
     - Returns 401 for expired token
     - Returns 401 for malformed token
     - Calls next() for valid token
     - Attaches decoded user to request context
```

The subagent sees a **self-contained task**. It has no way to discover other checkpoints because it was never told they exist. Scope is controlled by what information the main session feeds into the subagent.

## Design: cplus orchestrates, ECC subagents execute

```
cplus main session (owns the loop, state, and scope)
  │
  ├── Phase 1: ARCHITECT
  │     └── main session does planning (no subagent)
  │
  ├── Phase 2: SETUP
  │     └── main session does setup (no subagent)
  │
  ├── Phase 3: IMPLEMENTER (loop over checkpoints)
  │     │
  │     ├── Read checkpoint N from plan.md
  │     ├── Extract: description, files, acceptance criteria, test command
  │     ├── /tdd <checkpoint content pasted inline>     ← subagent, scoped
  │     ├── Subagent returns (code written, tests passing)
  │     ├── Main session updates state.md               ← cplus bookkeeping
  │     ├── Main session runs /compact                  ← cplus compaction
  │     └── Next checkpoint
  │
  ├── Phase 4: VERIFIER
  │     └── /verify full                                ← subagent, stateless
  │
  ├── Phase 5: REVIEWER
  │     ├── /code-review                                ← subagent, stateless
  │     └── /security-scan                              ← subagent, stateless
  │
  └── Phase 6: CLEANUP
        └── main session does cleanup (no subagent)
```

## ECC Command Safety Classification

| Command | Safe to delegate? | Why |
|---|---|---|
| `/tdd <inline content>` | Yes, with inline content | Subagent only sees the pasted task, can't expand scope |
| `/tdd <file reference>` | No | Subagent reads the file, discovers other checkpoints |
| `/plan` | No | Creates its own plan structure, conflicts with plan.md |
| `/code-review` | Yes | Operates on `git diff`, stateless |
| `/verify` | Yes | Runs build/type/lint/test, stateless |
| `/security-scan` | Yes | Scans current code, stateless |
| `/build-fix` | Yes | Fixes current build errors, stateless |

**The rule**: safe if the subagent can't discover scope beyond what you give it.

---

## Phase-by-Phase Design

### Phase 1: ARCHITECT

**Focus rules** (kept from v1):
- Follow only this phase's policy
- Forbidden: writing code, running tests
- Must produce plan.md with checkpoints

**What's new in v2**:
- Research-first approach (from ECC's development-workflow rule): run `gh search code` / `gh search repos` before designing
- Each checkpoint in plan.md must include a **self-contained description** suitable for passing to `/tdd`:

```markdown
## Checkpoint 1: JWT validation middleware

**Description**: Add middleware that validates JWT tokens from Authorization header.
**Files**: src/middleware/auth.ts, src/middleware/auth.test.ts
**Test command**: npm test src/middleware/auth.test.ts
**Acceptance criteria**:
- Returns 401 for missing token
- Returns 401 for expired token
- Returns 401 for malformed token
- Calls next() for valid token
- Attaches decoded user to request context
**Dependencies**: None
```

This format is critical — it makes checkpoints **copy-pasteable** into `/tdd` without needing plan.md context.

**Phase exit**:
- plan.md has self-contained checkpoints
- `/compact Setting up worktree for task <ID>. Plan: .cplus/tasks/<ID>/plan.md`

---

### Phase 2: SETUP (unchanged from v1)

No ECC integration needed. Already well-scoped.

**Phase exit**:
- `/compact Implementing checkpoint 1. Plan: .cplus/tasks/<ID>/plan.md`

---

### Phase 3: IMPLEMENTER (delegates to /tdd per checkpoint)

**Focus rules** (kept from v1):
- ONE checkpoint at a time
- Forbidden: scope expansion, skipping checkpoints
- Must update state.md

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

**ECC passive features active during this phase**:
- `post-edit-format` hook → auto-formats code the subagent writes
- `post-edit-typecheck` hook → immediate type error feedback
- `suggest-compact` hook → warns if context growing large
- `coding-style` rules → immutability, file organization
- `security` rules → no hardcoded secrets

---

### Phase 4: VERIFIER (uses /verify — safe, stateless)

**Focus rules** (kept from v1):
- Forbidden: implementing features, fixing bugs (document only)
- Must produce clear PASS/FAIL verdict

**ECC integration — `/verify` is safe here**:
- `/verify` is stateless — runs build/type/lint/test on current code
- Doesn't make scope decisions
- Produces a structured report

```
VERIFIER runs:
  1. /verify full                               ← ECC command (stateless)
  2. Copy verification report into .cplus/tasks/<ID>/report.md
  3. Add verdict: PASS / FAIL / PASS WITH ISSUES
  4. If FAIL: document specific failures for IMPLEMENTER to fix
```

If FAIL → return to IMPLEMENTER for the specific failing checkpoint only.

---

### Phase 5: REVIEWER (uses /code-review + /security-scan — safe, stateless)

**Focus rules** (kept from v1):
- Forbidden: changing requirements, large refactors
- Small fixes for critical issues only

**ECC integration — both commands are safe here**:
- `/code-review` operates on `git diff` — scoped to actual changes
- `/security-scan` operates on current codebase — stateless

```
REVIEWER runs:
  1. /code-review                               ← ECC command (scoped to git diff)
  2. /security-scan                             ← ECC command (stateless)
  3. Append findings to .cplus/tasks/<ID>/report.md
  4. Fix CRITICAL issues only (small fixes allowed)
  5. Document remaining issues for future work
```

---

### Phase 6: CLEANUP (unchanged from v1)

No ECC integration needed. Remove worktree, prune refs.

---

## Strategic Compaction Protocol

Phase transitions trigger `/compact` with context-preserving messages:

| Transition | Compact message |
|---|---|
| ARCHITECT → SETUP | `/compact Setting up worktree for task <ID>. Plan: .cplus/tasks/<ID>/plan.md` |
| SETUP → IMPLEMENTER | `/compact Implementing checkpoint 1. Plan: .cplus/tasks/<ID>/plan.md` |
| Checkpoint N → N+1 | `/compact Checkpoint N done. Starting N+1. State: .cplus/tasks/<ID>/state.md` |
| IMPLEMENTER → VERIFIER | `/compact Verifying implementation. State: .cplus/tasks/<ID>/state.md` |
| VERIFIER → REVIEWER | `/compact Reviewing code. Report: .cplus/tasks/<ID>/report.md` |
| REVIEWER → CLEANUP | `/compact Cleaning up task <ID>` |

Why this beats ECC's `suggest-compact` (fires after N tool calls): phase boundaries ARE the natural compaction points. No heuristic needed.

## Summary: What comes from where

| Concern | Owner | Mechanism |
|---|---|---|
| Phase transitions | cplus | develop-v2.md prompt |
| Role boundaries (Allowed/Forbidden) | cplus | develop-v2.md prompt |
| Checkpoint discipline | cplus | develop-v2.md prompt, main session loop |
| Checkpoint format (self-contained) | cplus | ARCHITECT phase requirement |
| TDD execution per checkpoint | ECC | /tdd command with inline content |
| Scope verification after /tdd | cplus | Main session checks subagent output |
| State management (state.md) | cplus | Main session bookkeeping |
| Memory hierarchy | cplus | develop-v2.md prompt |
| Workspace structure (.cplus/tasks/) | cplus | develop-v2.md prompt |
| Strategic compaction timing | cplus | Phase transitions → /compact |
| Verification (build/type/lint/test) | ECC | /verify command (stateless) |
| Code review | ECC | /code-review command (stateless) |
| Security scanning | ECC | /security-scan command (stateless) |
| Auto-formatting on edit | ECC | post-edit-format hook (passive) |
| Type checking on edit | ECC | post-edit-typecheck hook (passive) |
| Coding standards | ECC | Always-on rules (passive) |

## The principle

> **cplus controls the loop, scope, and state. ECC commands execute within that scope.**
>
> For stateful commands (/tdd): pass self-contained content inline, never file references.
> For stateless commands (/verify, /code-review): call directly, they can't expand scope.

## Checkpoint Format Spec

Every checkpoint in plan.md MUST be self-contained and copy-pasteable:

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

## Implementation Steps

1. Create `prompts/actions/develop-v2.md` based on current `develop.md`
2. Add checkpoint format spec to ARCHITECT phase
3. Replace IMPLEMENTER's "write code" with /tdd delegation loop
4. Add scope verification step after each /tdd call
5. Add `/verify` to VERIFIER phase
6. Add `/code-review` + `/security-scan` to REVIEWER phase
7. Add strategic compaction protocol at phase transitions
8. Add research-first approach to ARCHITECT phase
9. Update README with develop-v2 usage and ECC prerequisite
10. Test with a real spec end-to-end
