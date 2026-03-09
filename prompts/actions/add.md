# Action: Add

## Purpose
Guide the user through creating a new action or role prompt file through structured discovery, generation, and validation — producing output that matches cplus conventions and Claude Code best practices.

## Workflow

```
GATHERER → GENERATOR → VALIDATOR
```

Each phase has a clear responsibility and explicit handoff. Run all three in sequence, or invoke a single phase with `--roles`.

---

### Phase 1: GATHERER
**Goal**: Collect all inputs needed to generate a high-quality prompt

Ask whether the user is creating an **action** or a **role**, then ask the appropriate question set. Use `AskUserQuestion` with 2-4 concrete options for every decision — never ask open-ended questions. When all inputs are collected, show a structured summary and ask the user to confirm before proceeding.

**Outputs**:
- Confirmed input summary (name, type, purpose, workflow/persona, outputs, constraints)

---

### Phase 2: GENERATOR
**Goal**: Synthesize confirmed inputs into a complete, well-written prompt file

Do not fill in a template. Write the prompt from scratch as a coherent document. Apply the canonical schema for the type (action or role). Follow Claude Code prompt best practices: imperative voice, explicit boundaries, concrete outputs, no ambiguity. Show the complete generated file to the user for review before proceeding.

**Outputs**:
- Complete prompt file content shown to user

---

### Phase 3: VALIDATOR
**Goal**: Verify the generated prompt is structurally correct, high-quality, and ready to save

Run all structure, quality, and completeness checks. If issues are found, list them specifically and offer to fix automatically or return to GENERATOR. If all checks pass, show the target file path and ask the user to confirm the save.

**Outputs**:
- Saved file at `prompts/actions/<name>.md` or `prompts/roles/<name>.md`

---

## Output Contract

| Output | Format | Location |
|--------|--------|----------|
| Action file | Markdown | `prompts/actions/<name>.md` |
| Role file | Markdown | `prompts/roles/<name>.md` or `prompts/roles/<group>/<name>.md` |

Files are only written after explicit user confirmation. Warn and require overwrite confirmation if the path already exists.

## Phase Transition Format

After each phase, state:

```
✅ <PHASE> Complete

<summary of what was produced>

Proceed to <NEXT PHASE>?
```

User must confirm before the next phase begins.

## Examples

### Example 1: Creating a new role
```
cplus add --roles add/gatherer
# → Collects role requirements via structured Q&A
# → Summarizes: name=tester, persona=QA engineer, allowed=[run tests], ...
# → User confirms → proceed to generator
```

### Example 2: Full workflow
```
cplus add
# → Runs GATHERER → GENERATOR → VALIDATOR in sequence
# → Produces prompts/roles/tester.md after confirmation
```

## Out of Scope
- Editing existing actions or roles
- Generating multiple files in one run
- YAML frontmatter or metadata fields
- Linting or validating existing prompt files
