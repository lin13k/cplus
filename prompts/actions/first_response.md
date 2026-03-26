# Action: First Response

## Purpose

Given a raw goal and its interpretation, produce the first planning round: a design map, architecture outline, design questions, and initial task proposals.

## Input

You will receive a JSON object with:

- `raw_input` — the user's goal as typed
- `interpretation` — structured interpretation containing:
  - `summary` — concise restatement of the goal
  - `vision` — the intended end state
  - `design_focus` — key design domains to explore
  - `constraints` — known constraints
  - `assumptions` — assumptions made during interpretation
  - `unknowns` — unresolved questions from interpretation

## Instructions

1. **Synthesize the goal** — Distill the raw input and interpretation into a one-line goal summary.

2. **Map the design space** — Identify 5-10 high-level design domains or areas the project touches (e.g., data model, state management, API surface, UI layout).

3. **Outline the architecture** — List 5-10 key architectural modules or components needed. Each entry should name a distinct module and its responsibility.

4. **Generate design questions** — Produce 5-10 design questions that must be answered before implementation. Each question gets a unique ID (`DQ-001`, `DQ-002`, ...), an explanation of why it matters, and 2-4 suggested options or approaches. Surface every unknown from the interpretation as a design question — do not drop or skip unknowns.

5. **Propose initial tasks** — Produce 5-10 task proposals covering the first phase of work. Each task gets a unique ID (`TP-001`, `TP-002`, ...), a title, description, task type (e.g., `architecture`, `data_model`, `state_flow`, `ui`, `integration`), and a list of dependency IDs (empty if none).

## Output

If an output file path is specified in the "Output Requirement" section below, write the raw JSON object to that file. Otherwise, respond with **only** a valid JSON object below. No prose, no markdown fences, no commentary outside the JSON.

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
  ]
}
```

## Constraints

- Output must be valid, parseable JSON — no trailing commas, no comments
- Do not include fields outside the schema
- Every unknown from the interpretation must appear as a design question
- Aim for 5-10 design questions and 5-10 initial tasks
- Task dependencies must reference valid task IDs within the same output
- Design question IDs use the format `DQ-XXX`, task IDs use `TP-XXX`
- Keep entries concise — one sentence for descriptions, 2-4 words for suggested options
