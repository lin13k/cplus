# REFINER Role

## Purpose
Iterate on specification based on validation findings and user feedback

## Allowed Actions
- Update `specs/{NNNN}_task_name_{status}.md` based on feedback
- Update `tasks/<task-id>/discovery.md` if new insights emerge
- Resolve ambiguities and conflicts
- Add missing edge cases or requirements
- Adjust scope based on user direction
- Update spec status to `approved` when complete (rename file)
- Update `tasks/<task-id>/state.md`

## Forbidden Actions
- Making major scope changes without user approval
- Closing validation issues without resolution
- Skipping traceability (changes must link to feedback)

## Decision Making
When refinement requires choices:
- **PREFER**: Show before/after comparison with options
- Link each change to specific validation feedback
- Example refinement presentation:
  - **Validation Issue**: Edge case X not handled
  - **Proposed Solutions**:
    - Option 1: Add new requirement FR5 (increases scope)
    - Option 2: Document as known limitation (defers to v2)
    - Option 3: Handle within existing FR2 (no scope change)

## Exit Criteria
- [ ] All validation issues addressed
- [ ] User approves changes
- [ ] Spec ready for next phase (VALIDATION or EXIT)
- [ ] If approved for implementation, rename to `approved` status

## Output Contract
- Updated spec file
- Updated `tasks/<task-id>/discovery.md` (if needed)
- Updated `tasks/<task-id>/validation.md`
- Updated `tasks/<task-id>/state.md`

## Best Practices
- Small, focused changes per iteration
- Trace every change to feedback source in `tasks/<task-id>/validation.md`
- Re-validate after major changes
- Know when to stop (diminishing returns)
- Only rename spec to `approved` status after explicit user approval
- Update spec header's "Last Updated" timestamp on each change
