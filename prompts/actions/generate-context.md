# generate-context: Module Context Documentation Generator

Generate comprehensive context documentation for a module or directory, producing an `AGENT.md` and supporting `context/*.md` files that give AI agents deep understanding of the codebase.

## Usage

```bash
cplus generate-context <module-path>              # Full run: analyze → generate → validate
cplus generate-context <module-path> --dry-run    # Stop after ANALYZER phase (scope proposal only)
```

## Workflow

```
ANALYZER → GENERATOR → VALIDATOR
```

Three phases run within a single interactive session. Each phase uses a dedicated role prompt for instructions.

### Phase 1: ANALYZER

**Role**: `roles/generate-context/analyzer.md`

Reads the codebase, maps module structure, extracts data model, traces business flows, identifies integration points, collects decisions, and proposes output scope. Writes `analysis.md` and `state.md` to the task workspace.

**User checkpoint**: Confirms or adjusts the proposed scope before proceeding.

If `--dry-run` is set, stop here after writing `analysis.md`.

### Phase 2: GENERATOR

**Role**: `roles/generate-context/generator.md`

Reads `analysis.md` and produces `AGENT.md` plus approved `context/*.md` files. Only generates files that were approved in the ANALYZER scope. Updates the feature map.

### Phase 3: VALIDATOR

**Role**: `roles/generate-context/validator.md`

Checks generated files for accuracy, completeness, consistency, and freshness against the actual codebase. Outputs `validation.md` with a PASS/FAIL/PASS WITH ISSUES verdict.

**User checkpoint**: Reviews validation results. If issues found, VALIDATOR sends targeted rework back to GENERATOR.

## Phase Transitions

1. ANALYZER completes → user confirms scope → GENERATOR begins
2. GENERATOR completes → VALIDATOR begins automatically
3. VALIDATOR completes → user reviews verdict
   - PASS: done
   - PASS WITH ISSUES / FAIL: rework loop (GENERATOR fixes → VALIDATOR re-checks)

## Task Workspace

All intermediate files are written to `.cplus/tasks/generate-context-<module>/`:
- `state.md` — current phase, progress, blockers
- `analysis.md` — ANALYZER output
- `validation.md` — VALIDATOR output

## Output Files

Generated in the module directory:
- `AGENT.md` — primary context document
- `context/*.md` — detailed reference files (data-model, flows, integration-points, decisions)
