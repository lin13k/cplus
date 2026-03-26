# Action: Goal Interpret

Interpret a user's raw goal into a structured understanding. Produce a `GoalInterpretation` that downstream actions can consume.

## Input

A single raw goal string from the user — informal, possibly vague, possibly ambitious.

## Process

1. Read the raw goal carefully
2. Restate it as a concise summary — capture intent, not just words
3. Describe what success looks like (the vision)
4. Identify the key design areas that matter most for this goal
5. Note any constraints implied or stated
6. Make reasonable assumptions where the goal is ambiguous — list every assumption explicitly
7. Flag genuine unknowns that downstream actions should resolve

Do not ask clarifying questions. Make best-effort assumptions and document them. The goal is speed and unblocked forward progress — not perfection.

## Output — `GoalInterpretation`

If an output file path is specified in the "Output Requirement" section below, write the raw JSON object to that file. Otherwise, print it to the conversation.

```json
{
  "summary": "string — concise restatement of the goal",
  "vision": "string — what success looks like",
  "design_focus": ["string — key design areas to focus on"],
  "constraints": ["string — known constraints"],
  "assumptions": ["string — assumptions being made"],
  "unknowns": ["string — open questions or unknowns"]
}
```

### Field Guidelines

- **summary**: One sentence. Capture the core intent, not a paraphrase.
- **vision**: Describe the end state from the user's perspective. What do they see, use, or experience when this is done?
- **design_focus**: 2-5 areas. Be specific (e.g., "CLI argument parsing" not "architecture").
- **constraints**: Only include constraints that are stated or strongly implied. Empty list is fine.
- **assumptions**: Every ambiguity you resolved should appear here. Err on the side of listing too many.
- **unknowns**: Things that genuinely cannot be assumed — they need user input or exploration. Keep this list short; prefer making an assumption over flagging an unknown.

## Principles

- **Bias toward action**: An imperfect interpretation that moves forward is better than a perfect one that blocks on questions.
- **Make it concrete**: Vague goals get specific interpretations. "Make it better" becomes "Improve X by doing Y."
- **Respect scope**: Interpret what the user said, not what you think they should have said. Flag scope expansion as an assumption if you do it.
- **Pipeline-aware**: This output feeds downstream actions (plan, spec, implement). Structure your interpretation to be useful to them.

## Out of Scope

- Asking the user clarifying questions
- Writing files or saving artifacts
- Executing any part of the interpreted goal
- Modifying the goal based on feasibility analysis
