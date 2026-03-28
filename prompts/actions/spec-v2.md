# Specification Development Workflow V2: Plan Mode

Create detailed specifications through a structured discovery process, using Claude plan mode to enforce phase discipline.

## Philosophy

Develop specifications through concrete examples, not abstract requirements. When decisions are needed, **always offer 2-4 concrete options** instead of open-ended questions.

**What's different from spec v1**: Plan mode acts as a natural phase boundary. Discovery and validation happen _in plan mode_ (read-only, think-only). Specification and refinement happen _outside plan mode_ (write the spec). This prevents premature writing during discovery and premature editing during validation.

## Quick Start

1. **Input**: User provides rough idea or requirement
2. **Process**: Follow 4-phase workflow with plan mode transitions
3. **Output**: Complete specification at `.cplus/specs/<ID>-<feature-slug>.md`

## The 4-Phase Workflow

```
[PLAN MODE]          [EDIT MODE]          [PLAN MODE]          [EDIT MODE]
DISCOVERER    →    SPECIFIER      →     VALIDATOR      →      REFINER     → EXIT
 (read/ask)        (write draft)        (review/audit)       (fix/approve)
                                              ↑                    |
                                              └────────────────────┘
                                               (if issues found)
```

**Mode transitions**:
| Phase | Mode | Why |
|---|---|---|
| DISCOVERER | Plan mode | Forces thinking before writing. No spec files created yet. |
| SPECIFIER | Edit mode | Draft the spec — write files, define contracts. |
| VALIDATOR | Plan mode | Review without editing. Prevents fixing while auditing. |
| REFINER | Edit mode | Apply fixes, get approval, finalize. |

---

## Phase 1: DISCOVERER (Plan Mode)

**Enter**: `EnterPlanMode` at the start of the workflow.

**Goal**: Understand the problem through concrete examples before writing anything.

**What You Do**:
- Read the codebase to understand existing patterns and constraints
- Gather 3-5 concrete examples from the user (happy path, edge cases, errors)
- Extract rules and constraints from examples
- Map dependencies and integration points
- **Decision Protocol**: When unclear, offer 2-4 options via `AskUserQuestion`

**Allowed**:
- Read files, search code, explore the codebase
- Ask the user questions (prefer `AskUserQuestion` with options)
- Think through the problem in plan mode responses

**Forbidden**:
- Writing any files (plan mode enforces this)
- Making assumptions without validating with the user

**Outputs** (in plan mode responses, not files):
- List of concrete examples with expected behavior
- Extracted rules and constraints
- Questions answered and decisions made
- Proposed spec structure (section outline)

**Exit Criteria**:
- 3+ concrete examples gathered (happy path, edge case, error)
- Rules and constraints identified
- User confirms understanding is correct
- Ready to write the formal spec

**Transition**: `ExitPlanMode` → proceed to SPECIFIER

---

## Phase 2: SPECIFIER (Edit Mode)

**Enter**: After exiting plan mode from DISCOVERER.

**Goal**: Transform discoveries into a formal specification file.

**What You Do**:
- Create the spec file at `.cplus/specs/<ID>-<feature-slug>.md`
- Write functional requirements with Given/When/Then acceptance criteria
- Define API contracts and data shapes
- Document edge cases and out-of-scope items
- **Decision Protocol**: Present design alternatives with tradeoffs

**Allowed**:
- Write the spec file using the Specification Template below
- Create supporting diagrams or examples if needed

**Forbidden**:
- Skipping requirements discovered in Phase 1
- Adding requirements not discussed with the user
- Writing implementation code

**Outputs**:
- `.cplus/specs/<ID>-<feature-slug>.md` with status `draft`
- All functional requirements with acceptance criteria
- Clear boundaries (in-scope / out-of-scope)

**Exit Criteria**:
- Spec file written with all discovered requirements
- Every requirement has Given/When/Then acceptance criteria
- Edge cases and error handling documented
- Out of scope clearly listed

**Transition**: `EnterPlanMode` → proceed to VALIDATOR

---

## Phase 3: VALIDATOR (Plan Mode)

**Enter**: `EnterPlanMode` after SPECIFIER writes the draft.

**Goal**: Audit the specification for completeness and feasibility without editing it.

**What You Do**:
- Read the spec file and run the completeness checklist
- Check consistency across requirements
- Assess implementation risks and feasibility
- Identify gaps, conflicts, and ambiguities
- **Decision Protocol**: Categorize issues by severity and suggest resolution strategies

**Allowed**:
- Read the spec file and codebase
- Identify issues and document them in plan mode responses
- Ask the user about unclear requirements

**Forbidden**:
- Editing the spec file (plan mode enforces this)
- Fixing issues (that's the REFINER's job)

**Completeness Checklist**:
- [ ] Every functional requirement has acceptance criteria
- [ ] Edge cases are documented with handling strategies
- [ ] API contracts are fully defined (inputs, outputs, errors)
- [ ] Non-functional requirements are measurable
- [ ] Dependencies are identified
- [ ] Out of scope is explicit
- [ ] No conflicting requirements
- [ ] No ambiguous terms (or they're defined)
- [ ] Implementation is feasible with current architecture

**Outputs** (in plan mode responses, not files):
- Categorized findings: CRITICAL / MAJOR / MINOR
- Risk assessment
- Completeness score (checklist items passed / total)
- Specific changes needed for REFINER

**Exit Criteria**:
- All checklist items evaluated
- Findings categorized and actionable
- User acknowledges the findings

**Transition**: `ExitPlanMode` → proceed to REFINER

---

## Phase 4: REFINER (Edit Mode)

**Enter**: After exiting plan mode from VALIDATOR.

**Goal**: Address validation findings and get user approval.

**What You Do**:
- Fix each CRITICAL and MAJOR issue from VALIDATOR findings
- Show before/after for each change with options
- Add missing requirements
- Adjust scope based on user feedback
- Update spec status to `review` then `approved`
- **Decision Protocol**: For each fix, show what changed and offer alternatives

**Allowed**:
- Edit the spec file to address findings
- Ask the user for approval on changes
- Update the spec status

**Forbidden**:
- Introducing new requirements not discussed
- Removing requirements without user approval
- Marking as approved without explicit user sign-off

**Outputs**:
- Updated `.cplus/specs/<ID>-<feature-slug>.md` with status `approved`
- All CRITICAL and MAJOR issues resolved
- MINOR issues documented in Open Issues (if deferred)

**Exit Criteria**:
- All CRITICAL issues resolved
- All MAJOR issues resolved or explicitly deferred
- User explicitly approves the spec
- Spec status updated to `approved`

**If issues remain**: `EnterPlanMode` → return to VALIDATOR for re-audit

---

## Decision-Making Protocol

### The Golden Rule
**When you need user input, offer 2-4 concrete options.** Make it easy to select, not write.

### Bad Example
```
"What error handling approach would you prefer?"
```

### Good Example
Use `AskUserQuestion` tool:
```
Question: "How should we handle errors when the API fails?"
Options:
1. Silent failure with console logging
2. Toast notification to user with retry button
3. Modal dialog blocking further action
4. Throw exception and halt execution
```

### When to Offer Options
- **Always**: For design choices, approach selection, scope decisions
- **Rarely**: For simple clarifications ("Is X correct?" → Yes/No is fine)

### How to Structure Options
- Make options **mutually exclusive**
- Include **tradeoffs** in descriptions
- Provide **2-4 options** (not too few, not too many)
- Add context so user can decide without asking more

---

## Workspace Structure

All specifications are saved to the workspace:

```
.cplus/
└── specs/
    ├── 0001-feature-name.md
    ├── 0002-another-feature.md
    └── ...
```

**Naming Convention**:
- Format: `<ID>-<feature-slug>.md`
- ID: 4-digit sequential number (e.g., `0001`, `0002`)
- Slug: kebab-case, descriptive (e.g., `user-authentication`, `file-upload`)
- Example: `.cplus/specs/0001-user-authentication.md`

---

## Specification Template

```markdown
# Specification: <Feature Name>

**Status**: draft | review | approved
**Created**: YYYY-MM-DD
**Last Updated**: YYYY-MM-DD

## Overview
[1-2 sentence summary]

## Functional Requirements
### FR1: <Requirement Name>
- **Description**: [What it does]
- **Acceptance Criteria**:
  - Given [context], when [action], then [outcome]
  - ...
- **Priority**: Must-have | Should-have | Nice-to-have

### FR2: ...

## Non-Functional Requirements
- Performance: [e.g., "response time < 100ms"]
- Scalability: [e.g., "support 1000 concurrent users"]
- Maintainability: [e.g., "follow existing patterns"]

## API / Interface Contract
[If applicable: function signatures, data shapes, events]

## Dependencies
- Requires: [other features, external systems]
- Blocks: [what depends on this]

## Edge Cases & Error Handling
- Edge case 1: [scenario] → [handling strategy]
- ...

## Out of Scope
[Explicitly list what is NOT included]

## Open Issues
- [ ] Issue 1 - [description, expected resolution]
```

---

## Techniques

### 1. Example Mapping (DISCOVERER phase)
Start with concrete scenarios:
- Happy path (normal flow)
- Edge case (boundary conditions)
- Error case (what can go wrong)
- Integration (how it interacts with other features)

### 2. Progressive Elaboration (SPECIFIER phase)
Build in layers:
1. Core (must-have, 80% value)
2. Extensions (should-have, 15% value)
3. Enhancements (nice-to-have, 5% value)

### 3. Behavior-Driven Development (SPECIFIER phase)
Write acceptance criteria as:
```
Given [initial context]
When [action/event]
Then [expected outcome]
And [additional assertions]
```

---

## Common Pitfalls to Avoid

1. **Open-ended questions** → Use AskUserQuestion with options
2. **Writing during discovery** → Stay in plan mode, think first
3. **Editing during validation** → Stay in plan mode, audit only
4. **Premature specification** → Discover first, specify later
5. **Scope creep** → Be explicit about out-of-scope
6. **Ambiguity** → Define terms clearly
7. **Missing edge cases** → Think adversarially
8. **Skipping validation** → Always re-enter plan mode to audit
9. **Assumption debt** → Validate understanding with user

---

## Exit Criteria

Specification is **complete** when:
- [ ] All validation checks pass
- [ ] User explicitly approves the spec
- [ ] Implementation team can start without further clarification
- [ ] Edge cases and error handling are documented
- [ ] Spec status is `approved`
