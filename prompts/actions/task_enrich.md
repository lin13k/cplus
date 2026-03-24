# Action: task_enrich

## Purpose
Enrich a task's title and description to address gaps identified by a readiness assessment. Reads project context from goal docs, round docs, and source references to produce a well-informed enrichment.

## Input

```json
{
  "task": {
    "id": "string",
    "goal_id": "string",
    "round_id": "string",
    "title": "string",
    "description": "string | null",
    "task_type": "string",
    "status": "string",
    "parent_task_id": "string | null",
    "ready_for_handoff": false,
    "source_kind": "string | null",
    "source_ref": "string | null",
    "source_proposal_id": "string | null",
    "created_at": "string — ISO timestamp",
    "updated_at": "string — ISO timestamp"
  },
  "missing": ["string — items the readiness assessment flagged as missing"]
}
```

## Output — `TaskEnrichment`

```json
{
  "title": "string — improved task title",
  "description": "string — enriched description addressing all missing items"
}
```

Output raw JSON only. No markdown wrapping, no explanation text.

## Workflow

1. **Gather context.** Read the following files to understand the broader project context:
   - Goal round response: `.evora/goals/{goal_id}/rounds/{round_id}/response.md`
   - Goal round response data: `.evora/goals/{goal_id}/rounds/{round_id}/response.json`
   - If `source_kind` is `"round"` and `source_ref` is set, also read: `.evora/goals/{goal_id}/rounds/{source_ref}/response.json`
   - If `source_ref` points to a file path, read that file.

2. **Generate enrichment.** Produce a `TaskEnrichment` JSON object that:
   - Addresses every item in the `missing` array
   - Preserves the original intent and scope of the task
   - Rewrites the title to be specific and actionable
   - Writes a description that is self-contained — a developer should be able to start work from the description alone without reading the original proposal

## Constraints

- Every item in `missing` must be addressed in the enriched description. Do not skip any.
- Preserve the original task's intent and scope. Do not expand scope beyond what the task was meant to cover.
- The title must be concise (under 80 characters) and start with a verb.
- The description must be concrete: specify file paths, function signatures, data structures, or acceptance criteria where appropriate.
- Do not invent requirements that are not supported by the project context or the original task.
- Output must be valid JSON parseable by `JSON.parse()`.