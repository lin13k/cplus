# Specification Development Workflow

Create detailed specifications through a structured discovery process.

## Philosophy

Develop specifications through concrete examples, not abstract requirements. When decisions are needed, **always offer 2-4 concrete options** instead of open-ended questions.

## Quick Start

1. **Input**: User provides rough idea or requirement
2. **Process**: Follow 4-phase workflow (DISCOVERER → SPECIFIER → VALIDATOR → REFINER)
3. **Output**: Complete specification ready for implementation

## The 4-Phase Workflow

```
DISCOVERER → SPECIFIER → VALIDATOR → REFINER → [VALIDATOR or EXIT]
                                          ↑            |
                                          └────────────┘
                                           (if issues found)
```

### Phase 1: DISCOVERER
**Goal**: Understand the problem through concrete examples

**What You Do**:
- Gather 3-5 concrete examples (happy path, edge cases, errors)
- Extract rules and constraints from examples
- **Decision Protocol**: When unclear, offer options, not open questions

**Outputs**:
- Initial specification structure with examples
- Questions and clarifications needed

### Phase 2: SPECIFIER
**Goal**: Transform discoveries into formal requirements

**What You Do**:
- Write functional requirements with Given/When/Then criteria
- Define API contracts and data shapes
- Document edge cases and out-of-scope items
- **Decision Protocol**: Present design alternatives with tradeoffs

**Outputs**:
- Formal specification with acceptance criteria
- Clear boundaries (in-scope / out-of-scope)

### Phase 3: VALIDATOR
**Goal**: Ensure specification is complete and feasible

**What You Do**:
- Run completeness checklist
- Check consistency across requirements
- Assess implementation risks
- Identify gaps and conflicts
- **Decision Protocol**: Categorize issues and suggest resolution strategies

**Outputs**:
- Validation findings and risks
- Completeness assessment

### Phase 4: REFINER
**Goal**: Address validation findings and get user approval

**What You Do**:
- Fix ambiguities and conflicts
- Add missing requirements
- Adjust scope based on feedback
- Get explicit user approval
- **Decision Protocol**: Show before/after with options for each change

**Outputs**:
- Final approved specification
- Ready for implementation

## Decision-Making Protocol

### The Golden Rule
**When you need user input, offer 2-4 concrete options.** Make it easy to select, not write.

### Bad Example ❌
```
"What error handling approach would you prefer?"
```

### Good Example ✅
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

## Techniques

### 1. Example Mapping
Start with concrete scenarios:
- Happy path (normal flow)
- Edge case (boundary conditions)
- Error case (what can go wrong)
- Integration (how it interacts with other features)

### 2. Progressive Elaboration
Build in layers:
1. Core (must-have, 80% value)
2. Extensions (should-have, 15% value)
3. Enhancements (nice-to-have, 5% value)

### 3. Behavior-Driven Development (BDD)
Write acceptance criteria as:
```
Given [initial context]
When [action/event]
Then [expected outcome]
And [additional assertions]
```

## Common Pitfalls to Avoid

1. **Open-ended questions** → Use AskUserQuestion with options
2. **Premature specification** → Discover first, specify later
3. **Scope creep** → Be explicit about out-of-scope
4. **Ambiguity** → Define terms clearly
5. **Missing edge cases** → Think adversarially
6. **Assumption debt** → Validate understanding with user

## Exit Criteria

Specification is **complete** when:
- [ ] All validation checks pass
- [ ] User explicitly approves the spec
- [ ] Implementation team can start without further clarification
- [ ] Edge cases and error handling are documented
