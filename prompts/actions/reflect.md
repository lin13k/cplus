# Action: reflect

Analyze completed domain work against the original goal to identify specific gaps. Determine whether the domain is complete or needs a follow-up round.

## Input

```json
{
  "goal_id": "string — the goal ID",
  "domain_name": "string — name of the completed domain",
  "domain_description": "string — what the domain covers",
  "domain_item_ids": ["string — item IDs that were in this domain"],
  "completed_tasks": [
    {
      "id": "string — task ID",
      "title": "string",
      "status": "string — e.g. 'done', 'blocked'"
    }
  ],
  "instruction": "string — reflection criteria (provided by caller)"
}
```

## Output — `ReflectionResponse`

If an output file path is specified in the "Output Requirement" section below, write the raw JSON object to that file. Otherwise, output raw JSON only. No markdown wrapping, no explanation text.

```json
{
  "gaps": ["string — specific, actionable gap descriptions (empty array if none)"],
  "action": "string — 'complete' if no gaps, 'new_round' if gaps exist",
  "summary": "string — brief summary of the reflection"
}
```

## Workflow

1. **Gather context.** Read the goal and domain context to understand what the goal requires:
   - Goal response: `.evora/goals/{goal_id}/rounds/*/response.md` (most recent round)
   - Goal response data: `.evora/goals/{goal_id}/rounds/*/response.json` (most recent round)
   - Use `domain_description` and the `instruction` field for domain-specific evaluation criteria.

2. **Identify blocked tasks.** Any task with `status` of `"blocked"` is automatically a gap. For each blocked task, produce a gap description that names the task and its blocking condition.

3. **Evaluate goal alignment.** Compare the completed (non-blocked) tasks against the original goal's requirements for this domain. For each goal requirement not covered by a completed task, produce a gap description.

4. **Determine action.** If `gaps` is non-empty, set `action` to `"new_round"`. If `gaps` is empty, set `action` to `"complete"`.

5. **Write summary.** Produce a one-to-two sentence summary of the domain's completion state: what was achieved and what (if anything) remains.

## Constraints

- Every blocked task must appear as a gap. No exceptions.
- Gaps must be specific and actionable — not vague like "more work needed". Each gap must name what is missing and why it matters to the goal.
- If `gaps` is empty, `action` must be `"complete"`. The caller enforces this invariant, but the LLM must not contradict it.
- If `gaps` is non-empty, `action` must be `"new_round"`.
- Do not invent requirements that are not supported by the goal context. Only flag gaps for things the goal actually requires.
- The `instruction` field may narrow or broaden reflection criteria. Follow it when provided.
- Output must be valid JSON parseable by `JSON.parse()`.

## Principles

- **Goal-anchored**: Every gap must trace back to a specific goal requirement. Do not flag work that is outside the domain's scope.
- **Blocked = gap**: Blocked tasks represent unfinished work by definition. Always surface them.
- **No false completions**: When uncertain whether a requirement is covered, flag it as a gap. A redundant follow-up round costs less than a missed requirement.
- **No false gaps**: Do not manufacture gaps to justify another round. If the completed tasks satisfy the goal's requirements for this domain, the domain is complete.

## Out of Scope

- Executing follow-up work or creating new tasks
- Modifying completed task records
- Evaluating domains other than the one specified in the input
- Enriching or rewriting task descriptions
