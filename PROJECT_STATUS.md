# Project Status

Last updated: 2026-05-23

## Current Architecture Version

**v0.4-design** — refactored per `05_cc_revision_and_architecture_guide.md`

## Branch

Active development: `dev`
Stable: `main` (commit d6223f9 — Milestones 0–3 merged 2026-05-23)

## Module Status

| Module | Status | Notes |
| --- | --- | --- |
| `agentprof/schema/` | implemented | FROZEN — events, spans, observations, evidence |
| `agentprof/model/execution_model.py` | implemented | FROZEN — correlation graph only |
| `agentprof/model/observer_registry.py` | implemented | FROZEN — `from_yaml()` done |
| `agentprof/validator.py` | implemented | FROZEN — forbidden actions + budget |
| `agentprof/storage.py` | implemented | FROZEN — write/read events.jsonl |
| `agentprof/observers/base.py` | implemented | FROZEN — BaseObserver ABC |
| `agentprof/observers/backends/langchain/resource_snapshot.py` | implemented | psutil background thread |
| `agentprof/observers/backends/langchain/tool_events.py` | implemented | `wrap_tool()` done |
| `agentprof/observers/backends/langchain/llm_client_timing.py` | implemented | monkey-patches OpenAI client |
| `agentprof/observers/backends/langchain/semantic_langchain.py` | implemented | needs langchain_core at runtime |
| `agentprof/planner/base.py` | implemented | FROZEN — BasePlanner ABC |
| `agentprof/planner/backends/llm/llm_planner.py` | implemented | LLM call → JSON parse → ObservationPlan |
| `agentprof/planner/backends/llm/context_builder.py` | implemented | formats state → planner prompt |
| `agentprof/planner/backends/rule/rule_planner.py` | implemented | deterministic rule planner (ablation) |
| `agentprof/analysis/timeline.py` | implemented | start/end pairing → SpanRecord |
| `agentprof/analysis/breakdown.py` | implemented | llm/tool/wait split + multi-program aggregation |
| `agentprof/analysis/resource_health.py` | implemented | USE method on resource_snapshot.csv |
| `agentprof/analysis/questions.py` | implemented | generates diagnostic questions from breakdown + health |
| `agentprof/executor.py` | implemented | executes approved plan → EvidenceRecord |
| `agentprof/controller.py` | implemented | full run_profiling() loop |
| `agentprof/report/markdown_report.py` | implemented | 10-section report.md |
| `agentprof/report/summary_json.py` | implemented | summary.json |
| `agentprof/tools/run_workload_tool.py` | implemented | wires agent + observers + storage |
| `targets/langchain_react_agent/tools.py` | implemented | slow/cpu/flaky tools |
| `targets/langchain_react_agent/agent.py` | implemented | run_task() done; needs vLLM for live test |
| `baselines/langfuse_adapter/` | stub | comparison baseline a |
| `baselines/opentelemetry_adapter/` | stub | comparison baseline a |
| `baselines/rule_based_profiler/` | stub | ablation baseline b |

## Tests

66 tests passing (nusa100, langchain + vLLM available):

- `tests/test_schema.py` — schema construction + JSON roundtrip
- `tests/test_storage.py` — event read/write
- `tests/test_validator.py` — forbidden actions, budget
- `tests/test_analysis.py` — timeline, breakdown, multi-program aggregation, registry from_yaml
- `tests/test_milestone2.py` — resource_health, questions (18 tests)
- `tests/test_tools.py` — slow/cpu/flaky tool behavior + workload event tagging (8 tests)

End-to-end smoke test PASSED (rule planner, 3 workload programs, Qwen3-30B-A3B-Instruct-2507)

Run with:

```bash
conda activate agentprof
pytest tests/ -x -q
```

## Completed

- [x] Milestone 0: Repository skeleton
- [x] v0.4 architecture refactor
- [x] Milestone 1: observers, analysis (timeline, breakdown), ObserverRegistry.from_yaml() — 38 tests
- [x] Milestone 2: resource_health, questions, run_workload_tool, agent run_task(), end-to-end smoke test
- [x] Milestone 3: rule_planner, llm_planner, context_builder, executor, controller, report — full loop dry-run validated
- [x] Smoke test PASSED on nusa100 (rule planner + Qwen3-30B-A3B-Instruct-2507, 2026-05-23)
- [x] LLM planner smoke test PASSED on nusa100 (Qwen3-30B-A3B-Instruct-2507 → valid ObservationPlan JSON, 2026-05-23)
- [x] Milestone 4: controlled multi-program config verified; per-program/system breakdown aggregation implemented; report and summary expose per-program results

## In Progress

_(none — ready to start Milestone 5)_

## Next: Milestone 5

1. Select BFCL V3 multi-turn subset
2. Implement trace adapter for BFCL tasks
3. Compare report vs controlled workload

## Blocked

_(none recorded)_

## Known Unknowns

- BFCL V3 subset size and task selection criteria
- BFCL trace adapter shape and expected output schema
- Deep Agents SDK evaluation deferred
