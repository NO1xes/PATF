# experiments/designs/

Architecture Decision Records (ADRs) for AgentProf design decisions.

## What is an ADR?

An ADR documents a significant architectural decision: the context, the options considered, the decision made, and the consequences. Once accepted, an ADR is append-only — if the decision changes, write a new ADR that supersedes it.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [ADR-001](ADR-001-observer-interface.md) | Observer Interface Design (Interface + Backend pattern) | Accepted |
| [ADR-002](ADR-002-planner-interface.md) | Planner Interface Design (LLM vs rule-based ablation) | Accepted |

## When to write an ADR

- A design decision affects FROZEN or Interface-stable modules
- Two contributors disagree on an approach
- A significant architectural change is being considered
- A new backend or baseline is being added that changes the comparison structure

## Template

```markdown
# ADR-NNN: Title

- **Date**: YYYY-MM-DD
- **Status**: Proposed | Accepted | Superseded by ADR-NNN
- **Deciders**: GitHub handles of contributors involved

## Context
What problem are we solving? What constraints apply?

## Decision
What did we decide to do?

## Consequences
What becomes easier or harder as a result?
```

## Numbering

Use the next sequential number. Check this directory for the highest existing number before creating a new ADR.
