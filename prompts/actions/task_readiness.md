# Action: Task Readiness

## Purpose

Assess whether a task has enough detail and context to be handed off for execution. Evaluate description completeness, context sufficiency, and actionability — then return a structured verdict.

## Input

You will receive a JSON object with:

- `task` — the full task record:
  - `id` — unique task identifier
  - `goal_id` — parent goal identifier
  - `round_id` — planning round identifier
  - `title` — short task title
  - `description` — detailed task description (may be null)
  - `task_type` — category of work (e.g., `architecture`, `ui`, `data_model`)
  - `status` — current task status
  - `parent_task_id` — parent task identifier (null if top-level)
  - `ready_for_handoff` — current readiness flag (your job is to reassess this)
  - `source_kind` — origin type (may be null)
  - `source_ref` — origin reference (may be null)
  - `source_proposal_id` — originating proposal (may be null)
  - `created_at` — ISO timestamp
  - `updated_at` — ISO timestamp

- `context_docs` — array of relevant context documents (design docs, specs, prior round outputs)

## Instructions

Evaluate the task against three readiness dimensions:

1. **Description completeness** — Does the task have a non-null description that explains *what* needs to be done and *what done looks like*? A title alone is not sufficient. The description must be specific enough that an implementer would not need to ask clarifying questions about scope.

2. **Context sufficiency** — Do the provided `context_docs` contain enough background for an implementer to understand *why* this task exists, *where* it fits in the system, and *how* it relates to adjacent work? A task with a good description but no supporting context is not ready if the work requires architectural or domain knowledge not captured in the description itself.

3. **Actionability** — Is the task concrete enough to start immediately? It must have a clear entry point (what file, module, or system to touch), a defined scope boundary (what is and isn't included), and no unresolved blockers or dependencies that would prevent execution.

For each dimension that fails, add a specific entry to the `missing` array describing what is absent. For each missing item, also include a concrete suggestion for how to fix it — what to add, where to find it, or what question to answer.

A task is `ready` only when all three dimensions pass. If any dimension fails, set `ready` to `false`.

## Output

If an output file path is specified in the "Output Requirement" section below, write the raw JSON object to that file. Otherwise, respond with **only** a valid JSON object below. No prose, no markdown fences, no commentary outside the JSON.

```json
{
  "ready": true,
  "reason": "string — one-sentence explanation of the overall assessment",
  "missing": [
    {
      "dimension": "description | context | actionability",
      "gap": "string — what is missing",
      "suggestion": "string — concrete fix or next step to resolve"
    }
  ]
}
```

When `ready` is `true`, `missing` must be an empty array. When `ready` is `false`, `missing` must contain at least one entry.

## Constraints

- Output must be valid, parseable JSON — no trailing commas, no comments
- Do not include fields outside the schema
- Do not attempt to fix the task or rewrite its description — only assess and suggest
- Each `missing` entry must reference exactly one of the three dimensions
- Keep `reason` to a single sentence
- Keep `gap` and `suggestion` concise — one sentence each
- Be strict: when in doubt, mark as not ready. False positives (marking unready tasks as ready) are worse than false negatives
