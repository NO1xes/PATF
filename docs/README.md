# docs/

Design documents, weekly reports, and meeting notes.

## Structure

| Directory | Contents |
| --- | --- |
| `design/` | Architecture design docs, collaboration spec, onboarding guide |
| `weekly/` | Weekly progress reports (one file per week, `YYYY-MM-DD.md`) |

## Design docs

| File | Purpose | Audience |
| --- | --- | --- |
| `design/onboarding.md` | Module map, maintenance rules, CC task templates | New contributors, CC agents |
| `design/collaboration.md` | Formal collaboration spec: ownership tiers, branch strategy, versioning | Both contributors, CC |
| `design/agentprof_design.md` | Deep architecture design and call chain | Both contributors |

## Reading order for new contributors

1. `../README.md` — project overview (English) / `../README_zh.md` (Chinese)
2. `../AGENTS.md` — hard constraints; read before writing any code
3. `../PROJECT_STATUS.md` — current progress, what's blocked, next steps
4. `../COLLAB.md` — daily workflow: branch commands, PR flow, experiment ops (Chinese)
5. `design/onboarding.md` — full module map, doc maintenance rules, CC task templates
6. `design/collaboration.md` — formal spec: ownership tiers, branch strategy, versioning rules

## Weekly reports

One file per week, named `YYYY-MM-DD.md` (date of the weekly meeting).
Write before each group meeting. Template:

```markdown
# Weekly Report YYYY-MM-DD

## Done this week
## Blocked
## Next week
## Questions for meeting
```
