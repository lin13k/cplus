# Action: review_summarize

## Purpose
Summarize a review item (design question or task proposal) with tradeoffs and a recommended action, to help the user make review decisions quickly and confidently.

## Input

```json
{
  "item_type": "string — one of: design_question, task_proposal",
  "question": "string — the design question text (present when item_type is design_question)",
  "why_it_matters": "string — why this question is important (present when item_type is design_question)",
  "options": ["string — suggested options/approaches (present when item_type is design_question)"],
  "title": "string — task title (present when item_type is task_proposal)",
  "description": "string — task description (present when item_type is task_proposal)",
  "task_type": "string — e.g. architecture, data_model (present when item_type is task_proposal)",
  "depends_on": ["string — IDs of dependencies (present when item_type is task_proposal)"]
}
```

## Output — `ReviewItemSummary`

If an output file path is specified in the "Output Requirement" section below, write the raw JSON object to that file. Otherwise, output raw JSON only. No markdown wrapping, no explanation text.

```json
{
  "plain_summary": "string — 2-3 sentence plain-language explanation of what this item is about and why it matters",
  "tradeoffs": ["string — key tradeoffs to consider when deciding on this item"],
  "recommendation": "string — suggested action with reasoning"
}
```

### Recommendation values

- **Design questions**: one of `accept`, `defer`, `reject`, `expand`, `edit` — followed by reasoning.
- **Task proposals**: one of `accept`, `defer`, `reject`, `prioritize` — followed by reasoning.

## Workflow

1. **Read project context.** Gather context from relevant project files — goal docs, round docs, specs, or architecture docs — to ground the analysis in the project's actual state. Use the input's `item_type` and associated fields to determine which files are relevant.

2. **Analyze the item.** For each item type:
   - **Design questions**: Evaluate each option against project context. Identify tensions, dependencies, and second-order consequences. Weigh reversibility, complexity, and alignment with existing patterns.
   - **Task proposals**: Assess scope clarity, feasibility, dependency risk, and alignment with project goals. Consider whether the task is well-defined enough to hand off.

3. **Produce the summary.** Generate a `ReviewItemSummary` JSON object:
   - `plain_summary`: Write for a reviewer who hasn't read the raw item. Lead with what the item is, then why it matters. Two to three sentences.
   - `tradeoffs`: List the key tensions. Each tradeoff should name what is being traded against what. Aim for 2-4 items.
   - `recommendation`: State the suggested action and a one-sentence justification grounded in the tradeoffs.

## Constraints

- Output must be valid JSON parseable by `JSON.parse()`.
- The `plain_summary` must be self-contained — a reviewer should understand the item without reading the raw input.
- Each entry in `tradeoffs` must name a concrete tension, not a vague concern. Bad: "complexity". Good: "Adding a caching layer reduces latency but introduces invalidation complexity across the write path."
- The `recommendation` must use exactly one of the allowed action values for the item type.
- Do not invent context that is not supported by the project files or the input. If context is insufficient, state what is missing in the `plain_summary` and recommend `defer`.
- Do not expand scope beyond the item. Summarize and recommend; do not redesign or rewrite.

## Out of Scope

- Executing the recommended action
- Modifying or enriching the original item
- Creating new design questions or task proposals
- Rendering UI or formatting for display — the consumer handles presentation
