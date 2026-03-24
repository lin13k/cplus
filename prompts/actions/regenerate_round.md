# Action: Regenerate Round

## Purpose

Given a previous planning round and the user's review decisions, produce a refined next round. Accepted items are preserved verbatim. Everything else is regenerated holistically, incorporating the user's feedback to produce a coherent, improved round.

## Input

You will receive a JSON object with two top-level keys:

- `previous_round` — the output of the prior round, matching the `first_response` schema:
  - `goal_summary` — one-line goal summary
  - `design_map` — array of design domain strings
  - `architecture_outline` — array of architectural module strings
  - `design_questions` — array of `{ id, question, why_it_matters, suggested_options }`
  - `initial_tasks` — array of `{ id, title, description, task_type, depends_on }`

- `review_decisions` — array of user decisions, each containing:
  - `id` — unique decision ID
  - `goal_id` — parent goal reference
  - `round_id` — which round this decision applies to
  - `target_type` — one of: `section`, `question`, `task`
  - `target_ref` — ID of the target (e.g., `DQ-001`, `TP-002`, or a section name)
  - `action` — one of: `accept`, `edit`, `expand`, `defer`, `reject`, `prioritize`
  - `note` — optional user note providing context or direction
  - `created_at` — ISO timestamp

## Instructions

1. **Parse review decisions** — Group decisions by target type and action. Identify which items are accepted, which need changes, and which are removed.

2. **Preserve accepted items** — Any design question or task with an `accept` decision must appear in the output unchanged — same ID, same content, same position relative to other accepted items.

3. **Apply decision semantics**:
   - `accept` — preserve verbatim in output
   - `edit` — rewrite the item incorporating the user's note; keep the same ID
   - `expand` — break the item into multiple items or add depth; use new IDs for additions
   - `defer` — remove from this round (may appear in a future round)
   - `reject` — remove permanently; do not include in output
   - `prioritize` — move the item earlier in ordering and increase its detail level

4. **Regenerate holistically** — After applying decisions, regenerate the non-accepted portions of the round as a coherent whole. New or modified items should fit naturally alongside preserved items. Consider ripple effects: rejecting a task may invalidate dependencies; expanding a design question may surface new tasks.

5. **Continue ID numbering** — New items must use IDs that continue from the highest ID in the previous round. If the previous round ended at `DQ-007`, new design questions start at `DQ-008`. Same logic for `TP-XXX` task IDs. Never reuse or reassign an existing ID.

6. **Update dependencies** — Revalidate all `depends_on` references. Remove references to rejected or deferred items. Add dependencies on new items where appropriate.

7. **Compile changes** — Produce a `changes` array summarizing every difference from the previous round. Each entry describes one addition, removal, or modification.

## Output

Respond with **only** a valid JSON object matching this schema. No prose, no markdown fences, no commentary outside the JSON.

```json
{
  "goal_summary": "string",
  "design_map": ["string"],
  "architecture_outline": ["string"],
  "design_questions": [
    {
      "id": "string",
      "question": "string",
      "why_it_matters": "string",
      "suggested_options": ["string"]
    }
  ],
  "initial_tasks": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "task_type": "string",
      "depends_on": ["string"]
    }
  ],
  "changes": [
    {
      "type": "string — one of: added, removed, modified, preserved, reordered",
      "target_ref": "string — ID or section name affected",
      "description": "string — what changed and why"
    }
  ]
}
```

## Constraints

- Output must be valid, parseable JSON — no trailing commas, no comments
- Do not include fields outside the schema
- Accepted items must appear verbatim — do not alter their content
- New IDs must continue from the previous round's highest ID per prefix
- All `depends_on` references must point to valid IDs in the current output
- Design question IDs use the format `DQ-XXX`, task IDs use `TP-XXX`
- The `changes` array must account for every difference from the previous round
- Deferred and rejected items must not appear in the main output arrays
- Keep entries concise — one sentence for descriptions, 2-4 words for suggested options

## Out of Scope

- Asking the user clarifying questions — use the review decisions as-is
- Writing files or saving artifacts beyond the JSON output
- Executing any tasks
- Modifying the goal summary unless a section-level decision targets it
