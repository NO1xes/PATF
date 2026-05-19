# Project Status

Last updated: 2026-05-19

## Current Architecture Version

**v0.4-design** — refactored per `05_cc_revision_and_architecture_guide.md`

## Completed

- [x] Milestone 0: Repository skeleton (v0.1, commit 8323a7a on main)
- [x] v0.4 architecture refactor (branch `refactor/v0.4-architecture`):
  - `agentprof/schema/` package: events, spans, observations, evidence
  - `agentprof/model/` package: ExecutionModel (correlation graph), ObserverRegistry + ObserverCapability
  - `agentprof/analysis/` package: timeline, breakdown, resource_health, questions (stubs)
  - `agentprof/planner/` package: llm_planner, prompts, context_builder (stubs)
  - `agentprof/tools/` package: run_workload, inspect_trace, query_observer, build_report (stubs)
  - `agentprof/validator.py`: forbidden action enforcement (implemented)
  - `agentprof/executor.py`: ObservationPlan execution (stub)
  - `agentprof/storage.py`: event read/write utilities (implemented)
  - `agentprof/observers/tool_events.py`: renamed from tool_wrapper, capability-driven
  - `agentprof/observers/resource_snapshot.py`: early baseline resource observer (stub)
  - `agentprof/report/` package: markdown_report, summary_json (stubs)
  - Updated `configs/profiling_spec.yaml`: forbidden_actions + initial_baseline
  - Updated `configs/observers.yaml`: capabilities + mode fields
  - Updated `AGENTS.md`, `state.py`, `controller.py`

## In Progress

- [ ] Merge `refactor/v0.4-architecture` → `main` after review

## Blocked / Pending

- [ ] **vLLM backend**: requires GPU server (not available on local PC)
- [ ] Conda environment creation pending

## Next: Milestone 1 (implement observers)

1. `agentprof/observers/semantic_langchain.py` — implement LangChain callbacks
2. `agentprof/observers/llm_client_timing.py` — implement client monkey-patch
3. `agentprof/observers/tool_events.py` — implement wrap_tool
4. `agentprof/observers/resource_snapshot.py` — implement psutil sampling
5. `agentprof/analysis/timeline.py` + `breakdown.py` — implement deterministic analysis
6. `agentprof/storage.py` — already implemented, verify
7. Run slow/cpu/flaky tasks and produce first `events.jsonl`

## Architecture Snapshot (v0.4)

```text
AgentProf = LLM planner + deterministic tools + validator

Target Agent  ──callbacks/wrappers──→  AgentProf observers
                                            ↓
                                      events.jsonl
                                            ↓
                                      analysis/ (timeline, breakdown, resource_health, questions)
                                            ↓
                                      planner/ (LLM generates ObservationPlan)
                                            ↓
                                      validator (approve/reject)
                                            ↓
                                      executor (run plan)
                                            ↓
                                      report/ (report.md, known_unknowns)
```

## Known Unknowns

- Which GPU server? Who sets up vLLM?
- LangChain callback API compatibility with LangGraph to be verified
- ObserverRegistry.from_yaml() not yet implemented
