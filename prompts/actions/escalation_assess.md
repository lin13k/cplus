# Action: escalation_assess

For each DQ/TP in a domain, assess whether the agent can auto-resolve it or must escalate to the human. Evaluate four dimensions: reversibility, blast radius, ambiguity, and tech-vs-business. Conservative default: when uncertain, escalate.

## Input

```json
{
  "goal_summary": "string — the goal's summary",
  "domain_name": "string — name of the domain being assessed",
  "domain_description": "string — what the domain covers",
  "items": [
    {
      "type": "string — 'dq' or 'tp'",
      "id": "string — item ID",
      "text": "string — question text or 'title: description'",
      "options": ["string — suggested options (present for DQs, absent for TPs)"]
    }
  ],
  "instruction": "string — assessment criteria (provided by caller)"
}
```

## Output — `EscalationResponse`

If an output file path is specified in the "Output Requirement" section below, write the raw JSON object to that file. Otherwise, output raw JSON only. No markdown wrapping, no explanation text.

```json
{
  "assessments": [
    {
      "item_id": "string — the item's ID",
      "item_type": "string — 'dq' or 'tp'",
      "level": "string — 'auto' or 'escalate'",
      "reasoning": "string — explanation of the assessment across the four dimensions",
      "agent_recommendation": "string — what the agent would choose if auto-resolving"
    }
  ]
}
```

## Workflow

1. **Read the goal summary and domain context.** Understand the project's intent and what the domain covers. Use the `instruction` field for any caller-specific assessment criteria.

2. **Evaluate each item on four dimensions.** For every DQ and TP in the input, assess:
   - **Reversibility** — Can the decision be easily undone? A database migration is low reversibility; a config flag is high.
   - **Blast radius** — How much of the system does this affect? A single module is low; cross-cutting concerns are high.
   - **Ambiguity** — Is there a clearly correct answer, or are multiple valid approaches in tension? Clear best practices are low ambiguity; trade-offs without obvious winners are high.
   - **Tech-vs-business** — Is this a purely technical decision, or does it involve business logic, user experience, or product strategy?

3. **Assign escalation level.** Apply the decision rules to determine `auto` or `escalate` for each item.

4. **Provide agent recommendation.** For every item — regardless of escalation level — state what the agent would choose if auto-resolving. For DQs with options, select from the provided options. For TPs, describe the implementation approach.

## Decision Rules

- **auto**: Technical decisions with low blast radius and high reversibility. The correct choice is clear from project context or established best practices.
- **escalate**: Business decisions, high blast radius, low reversibility, or ambiguous choices where multiple valid approaches exist. When the instruction provides domain-specific criteria, apply those as additional escalation triggers.
- **When uncertain → escalate.** The cost of an unnecessary escalation is low; the cost of a wrong autonomous decision is high.

## Constraints

- Every item in the input must have a corresponding assessment. No item left unassessed.
- The `level` field must be exactly `"auto"` or `"escalate"`. No other values.
- The `reasoning` field must reference at least two of the four dimensions explicitly.
- The `agent_recommendation` field must be concrete and actionable, not hedged or vague.
- Output must be valid JSON parseable by `JSON.parse()`.

## Principles

- **Conservative by default**: Err on the side of escalation. A human reviewing an easy question costs minutes; an agent making a wrong business call costs days.
- **Respect the instruction**: The `instruction` field may tighten or loosen assessment criteria. Follow it when provided.
- **Consistency**: Similar items in the same domain should receive similar assessments. If two DQs ask about the same concern from different angles, they should share an escalation level.
- **Transparency**: The reasoning must be honest about uncertainty. Do not manufacture confidence to justify `auto`.

## Out of Scope

- Resolving or answering the DQs/TPs themselves (only assess escalation level)
- Modifying, rewriting, or enriching the items
- Creating new items or domains
- Executing any implementation work
