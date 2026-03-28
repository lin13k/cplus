# Action: domain_cluster

Group a flat list of discovery questions (DQs) and task proposals (TPs) into 3–6 coherent domains. Each domain represents a distinct area of concern. Every item is assigned to exactly one domain. Domains are priority-ordered for implementation sequencing.

## Input

```json
{
  "goal_summary": "string — the goal's summary from the round",
  "items": [
    {"type": "dq", "id": "DQ-001", "text": "question text"},
    {"type": "tp", "id": "TP-001", "text": "title: description"}
  ],
  "instruction": "string — the grouping prompt"
}
```

## Output — `DomainClustering`

If an output file path is specified in the "Output Requirement" section below, write the raw JSON object to that file. Otherwise, output raw JSON only. No markdown wrapping, no explanation text.

```json
{
  "domains": [
    {
      "name": "string — short domain label (e.g., 'Data Model', 'Auth')",
      "description": "string — one-line description of what this domain covers",
      "rationale": "string — one sentence explaining why these items belong together",
      "priority": 1,
      "item_ids": ["DQ-001", "TP-001", "TP-002"]
    }
  ]
}
```

## Workflow

1. **Read the goal summary and instruction.** Understand the project context and what kind of grouping the instruction requests.

2. **Scan all items.** Read every DQ and TP. Identify natural clusters by area of concern — look for shared topics, dependencies, or implementation proximity.

3. **Form domains.** Create 3–6 domains. Each domain must have:
   - A short, descriptive name (2–3 words)
   - A one-line description of its scope
   - A one-sentence rationale for the grouping

4. **Assign every item.** Place each item into exactly one domain. If an item could fit multiple domains, assign it to the one where it has the strongest dependency or highest impact.

5. **Handle ambiguous items.** Items that do not fit cleanly into any domain go into a "General" catchall domain. The General domain should only exist if needed — do not create it preemptively.

6. **Priority-order domains.** Assign priority 1 to the domain that should be implemented first (highest foundational value or most blocking), and so on. Consider dependency order: domains that other domains depend on get higher priority.

## Constraints

- Produce exactly 3–6 domains. If the items naturally cluster into fewer than 3, combine related concerns. If more than 6, merge the least distinct domains.
- Every item in the input must appear in exactly one domain's `item_ids`. No item left unassigned, no item duplicated.
- Domain names must be unique within the output.
- Priority values must be sequential integers starting at 1 with no gaps.
- The "General" catchall domain, if present, must have the lowest priority (highest number).
- Output must be valid JSON parseable by `JSON.parse()`.

## Principles

- **Cohesion over balance**: A domain with 1 item is fine if that item is genuinely distinct. Do not pad domains for even distribution.
- **Implementation-aware grouping**: Group by what a developer would work on together, not by abstract taxonomy.
- **Respect the instruction**: The `instruction` field may contain specific grouping guidance. Follow it when provided.
- **Deterministic feel**: Given the same inputs, the clustering should be stable and unsurprising.

## Out of Scope

- Modifying, rewriting, or enriching the items themselves
- Creating sub-domains or hierarchical groupings
- Asking the user clarifying questions
- Executing any implementation work
