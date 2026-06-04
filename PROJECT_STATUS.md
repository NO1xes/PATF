# Project Status

Last updated: 2026-06-04

## Current Architecture Version

**v2-design** — ReAct tool-calling loop with four-tier profiling tools (see `docs/design/agentprof_design.md`)

## Branch

Active development: `feat/NO1xes-agent-loop-redesign` (v2 ReAct loop)
Integration: `dev`
Stable: `main`

## Module Status

| Module | Status | Notes |
| --- | --- | --- |
| `agentprof/schema/` | implemented | FROZEN — events, spans, observations, evidence |
| `agentprof/model/execution_model.py` | implemented | FROZEN — correlation graph only |
| `agentprof/model/observer_registry.py` | implemented | FROZEN — `from_yaml()` done |
| `agentprof/validator.py` | implemented | FROZEN — forbidden actions + budget |
| `agentprof/storage.py` | implemented | FROZEN — write/read events.jsonl |
| `agentprof/observers/base.py` | implemented | FROZEN — BaseObserver ABC |
| `agentprof/observers/backends/langchain/` | implemented | 4 baseline observers |
| `agentprof/planner/base.py` | implemented | FROZEN — BasePlanner ABC |
| `agentprof/planner/backends/llm/prompts_v2.py` | **implemented** | v2 system prompt + context builder |
| `agentprof/planner/backends/llm/llm_planner.py` | implemented | v0.4 legacy |
| `agentprof/planner/backends/rule/rule_planner.py` | implemented | v0.4 ablation |
| `agentprof/analysis/` | implemented | timeline, breakdown, resource_health, questions |
| `agentprof/tools/system_metrics.py` | **implemented** | L1 — 4 hardware tools (psutil + nvidia-smi) |
| `agentprof/tools/llm_serving_metrics.py` | **implemented** | L2 — 2 vLLM Prometheus tools |
| `agentprof/tools/tool_execution_metrics.py` | **implemented** | L3 — 3 span/event tools |
| `agentprof/tools/agent_semantic_metrics.py` | **implemented** | L4 — 2 agent trace tools |
| `agentprof/controller_v2.py` | **implemented** | ReAct tool-calling loop (v2 main entry) |
| `agentprof/controller.py` | implemented | v0.4 legacy linear pipeline |
| `agentprof/executor.py` | implemented | v0.4 legacy |
| `agentprof/report/` | implemented | markdown_report, summary_json |
| `agentprof/adapters/bfcl.py` | implemented | BFCL → workload YAML |
| `targets/langchain_react_agent/` | implemented | toy tools (slow/cpu/flaky) |

## Tests

90 tests passing (nusa100, no GPU needed for unit tests):

- `tests/test_schema.py` — schema construction + JSON roundtrip
- `tests/test_storage.py` — event read/write
- `tests/test_validator.py` — forbidden actions, budget
- `tests/test_analysis.py` — timeline, breakdown, multi-program aggregation, registry from_yaml
- `tests/test_milestone2.py` — resource_health, questions (18 tests)
- `tests/test_tools.py` — slow/cpu/flaky tool behavior (8 tests)
- `tests/test_bfcl_adapter.py` — BFCL workload adapter (4 tests)
- `tests/test_report.py` — multi-program report structure (2 tests)
- `tests/test_controller.py` — controller dry-run (1 test)
- `tests/test_system_metrics.py` — L1 hardware tools (4 tests)
- `tests/test_controller_v2.py` — v2 ReAct prompts + tool registry (6 tests)
- `tests/test_layers_2_4.py` — L2-L4 tools (8 tests)

Tier 0 ReAct profiling session PASSED (DeepSeek v4-pro, 5 tool calls, coherent drill-down report).

Run with:
```bash
conda run -n agentprof pytest tests/ -x -q
```

## Completed

- [x] Milestone 0–4: repository skeleton, observers, analysis, LLM planner, controller, report
- [x] v0.4 architecture (linear pipeline: baseline → analysis → planner → validator → executor)
- [x] Milestone 5 partial: BFCL adapter implemented
- [x] **v2 architecture**: ReAct tool-calling loop with 4-tier profiling tools (11 tools across L1-L4)

## In Progress

- v2: controlled target agent profiling test (slow/cpu/flaky toy tools → verify LLM identifies artificial bottlenecks)
- v2: end-to-end test with real benchmark (SWE-bench / TheAgentCompany)

## Next

1. Run controlled target agent + AgentProf v2 profiling (verify bottleneck identification)
2. Set up Docker sandbox for real benchmark experiments
