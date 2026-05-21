# Project Status

Last updated: 2026-05-20

## Current Architecture Version

**v0.4-design** — refactored per `05_cc_revision_and_architecture_guide.md`

## Branch

Active development: `refactor/v0.4-architecture` (latest commit: cd1c1b3)
Stable: `main` (commit 8323a7a, v0.1 skeleton — merge pending review)

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
| `agentprof/planner/backends/llm/llm_planner.py` | stub | Milestone 3, needs LLM |
| `agentprof/planner/backends/llm/context_builder.py` | stub | Milestone 3 |
| `agentprof/planner/backends/rule/rule_planner.py` | stub | Milestone 2, ablation baseline |
| `agentprof/analysis/timeline.py` | implemented | start/end pairing → SpanRecord |
| `agentprof/analysis/breakdown.py` | implemented | llm/tool/wait split |
| `agentprof/analysis/resource_health.py` | stub | Milestone 2 |
| `agentprof/analysis/questions.py` | stub | Milestone 2 |
| `agentprof/executor.py` | stub | Milestone 3 |
| `agentprof/controller.py` | stub | Milestone 3 |
| `agentprof/report/` | stub | Milestone 4 |
| `agentprof/tools/run_workload_tool.py` | stub | Milestone 2 |
| `targets/langchain_react_agent/tools.py` | implemented | slow/cpu/flaky tools |
| `targets/langchain_react_agent/agent.py` | stub | needs langchain + vLLM |
| `baselines/langfuse_adapter/` | stub | comparison baseline a |
| `baselines/opentelemetry_adapter/` | stub | comparison baseline a |
| `baselines/rule_based_profiler/` | stub | ablation baseline b |

## Tests

38 tests passing (no LLM/GPU required):

- `tests/test_schema.py` — schema construction + JSON roundtrip
- `tests/test_storage.py` — event read/write
- `tests/test_validator.py` — forbidden actions, budget
- `tests/test_analysis.py` — timeline, breakdown, registry from_yaml

Pending (needs langchain):

- `tests/test_tools.py` — slow/cpu/flaky tool behavior

Run with:

```bash
conda activate agentprof
pytest tests/test_schema.py tests/test_storage.py tests/test_validator.py tests/test_analysis.py -v
```

## Completed

- [x] Milestone 0: Repository skeleton
- [x] v0.4 architecture refactor
- [x] Milestone 1: observers (resource_snapshot, tool_events, llm_client_timing, semantic_langchain), analysis (timeline, breakdown), ObserverRegistry.from_yaml()

## In Progress

- [ ] Merge `refactor/v0.4-architecture` → `main` after review

## Next: Milestone 2

1. `agentprof/analysis/resource_health.py` — USE method on resource_snapshot.csv
2. `agentprof/analysis/questions.py` — generate diagnostic questions from breakdown
3. `agentprof/tools/run_workload_tool.py` — run target agent, collect events.jsonl
4. `targets/langchain_react_agent/agent.py` — implement `run_task()` (needs langchain + vLLM)
5. End-to-end smoke test: run slow_001 task → events.jsonl → timeline.csv → breakdown.json

## Blocked

- **langchain/langgraph not installed on local_pc** — network issues with China mainland mirrors; install on overseas server
- **vLLM backend** — requires GPU server (not available on local_pc)
- Framework decision pending: LangChain ReAct vs LangGraph Deep Agents SDK (see AGENTS.md)

## Known Unknowns

- Which GPU server? Who sets up vLLM?
- LangChain callback API compatibility with LangGraph to be verified on overseas server
- Deep Agents SDK evaluation deferred until overseas server available

