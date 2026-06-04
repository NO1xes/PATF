# Changelog

All notable changes to AgentProf are recorded here.
Format: `YYYY-MM-DD | type | description`
Types: `feat` / `fix` / `docs` / `exp` / `refactor` / `chore`

---

## 2026-06-04 | feat | v2 ReAct tool-calling loop with four-tier profiling tools

- Added `agentprof/controller_v2.py`: LLM-driven ReAct profiling loop (replaces linear v0.4 pipeline)
- Added `agentprof/planner/backends/llm/prompts_v2.py`: system prompt with 4-tier hierarchy + coarse→fine methodology
- Added `agentprof/tools/system_metrics.py`: L1 — 4 hardware tools (CPU/mem/disk/net, processes, GPU, time-series sampling)
- Added `agentprof/tools/llm_serving_metrics.py`: L2 — 2 vLLM Prometheus tools (snapshot + time-series)
- Added `agentprof/tools/tool_execution_metrics.py`: L3 — 3 span/event inspection tools (tool calls, span detail, event query)
- Added `agentprof/tools/agent_semantic_metrics.py`: L4 — 2 agent trace tools (list agents, trace loop)
- Updated `docs/design/agentprof_design.md` with v2 architecture (deployment topology, ReAct diagram, 4 tiers)
- Tier 0 test PASSED: DeepSeek v4-pro, 5 tool calls, coherent coarse→fine drill-down report
- 90/90 tests passing

## 2026-05-31 | fix | BFCL adapter handles .json files that are newline-delimited JSON

- `agentprof/adapters/bfcl.py`: `load_bfcl_cases()` now tries `json.loads()` first, falls back to line-by-line JSONL parsing on `JSONDecodeError`
- BFCL v3 `.json` question files work without renaming

## 2026-05-27 | test | Report structure regression tests

- Added `tests/test_report.py` for `report.md` and `summary.json` multi-program output structure
- Added `tests/test_controller.py` for controller dry-run with fixture events and rule planner
- Marked the report snapshot/structure test roadmap item complete in `TODO.md`
- Marked the controller dry-run test roadmap item complete in `TODO.md`

## 2026-05-27 | chore | Safe GitHub PAT push workflow

- Added `scripts/git_push_with_env_pat.sh` to push over HTTPS using `GITHUB_USER`/`GITHUB_PAT` from `.env` without embedding PATs in remote URLs
- Updated shared-server setup, onboarding, README, and security docs to forbid PAT-in-URL clone/push flows
- Updated `.env.example`, `AGENTS.md`, and `scripts/README.md` with the safe PAT workflow

## 2026-05-27 | feat | BFCL demo workload adapter

- Added `agentprof/adapters/bfcl.py` to convert BFCL JSON/JSONL question files into AgentProf workload YAML
- Added draft `configs/bfcl_demo_subset.yaml` for Milestone 5 demo subset selection and adapter command
- Added local BFCL fixture and adapter tests; no BFCL execution, vLLM, Docker, GPU, or external API calls
- Updated module/config documentation and Milestone 5 TODO status

## 2026-05-23 | feat | Milestone 4 — multi-program breakdown aggregation

- `agentprof/analysis/breakdown.py`: added system-level multi-program aggregation while preserving existing top-level llm/tool/wait/unknown fields
- `run_workload_tool.py`: flushes event observers after each workload program and tags events with the current `program_id`
- `report/markdown_report.py` and `report/summary_json.py`: include per-program breakdown and slowest-program summary
- Added 3 unit tests for per-program aggregation, slowest-program reporting, and workload event program tagging
- `TODO.md`: added post-Milestone 4 test roadmap and two-person task split for BFCL/demo/baseline work
- `COLLAB.md` and `docs/design/collaboration.md`: clarified sequential PR, semantic conflict resolution, and maintainer self-merge review expectations
- `baselines/README.md` and `experiments/comparisons/README.md`: expanded qualitative baseline candidate pool and comparison style
- Verified: 66/66 tests pass with `/disk2/runyuan/envs/agentprof/bin/python -m pytest tests/ -x -q`

## 2026-05-23 | chore | v0.1.1 — MIT LICENSE + open-source prep

- Added `LICENSE` (MIT)
- `README.md`, `README_zh.md`: added license section and link

## 2026-05-23 | exp | LLM planner smoke test PASSED

- `AGENTPROF_PLANNER=llm` end-to-end run on nusa100 (Qwen3-30B-A3B-Instruct-2507, port 18796)
- LLM generated 2 valid ObservationPlan JSON objects (plan_q001_01, plan_q002_01)
- Plans focused on tool_events + tool_process; both approved by validator
- Breakdown: tool 64% / llm 36%, 6 tool calls, 2 errors — consistent with rule-planner run
- run_id: run_fd052729 (local only, not committed)

## 2026-05-23 | fix | smoke test fixes — dotenv, tool wrap, vllm tool-call-parser

- `controller.py`: add `load_dotenv()` so `.env` is loaded before os.environ reads
- `controller.py`: set `state.timeline_path` after build_timeline
- `run_workload_tool.py`: use `llm.root_client` (not `llm.client`) for LLMClientTimingObserver
- `tool_events.py` `wrap_tool()`: handle LangChain StructuredTool by wrapping inner `.func`
  and rebuilding StructuredTool — fixes `'StructuredTool' is not callable` error
- `start_vllm.sh`: add `--enable-auto-tool-choice --tool-call-parser hermes`
  (required for Qwen3 MoE tool calling with vLLM)
- End-to-end smoke test PASSED: rule planner, 3 programs (slow/cpu/flaky)
  → tool 65% / llm 35%, 6 tool calls, 2 errors, report.md generated correctly
- 63/63 tests passing (test_tools.py now runs with langchain available on nusa100)

## 2026-05-23 | feat | Milestone 3 — full controller loop + LLM planner + report

- Implemented `agentprof/planner/backends/rule/rule_planner.py` — deterministic rule planner (tool/llm/error heuristics)
- Implemented `agentprof/executor.py` — executes approved ObservationPlan, appends EvidenceRecord to state
- Implemented `agentprof/planner/backends/llm/context_builder.py` — formats ProfilingState into LLM prompt context
- Implemented `agentprof/planner/backends/llm/llm_planner.py` — LLM call → JSON parse → ObservationPlan
- Implemented `agentprof/report/markdown_report.py` — 10-section report.md (scope, workload, breakdown, health, evidence, unknowns)
- Implemented `agentprof/report/summary_json.py` — summary.json
- Implemented `agentprof/controller.py` — full `run_profiling()` loop: baseline → analysis → questions → plan → validate → execute → report
- Dry-run validated on sample_events.jsonl + rule planner (no vLLM required)
- 56/56 tests passing; full import chain verified



- Implemented `agentprof/analysis/resource_health.py` — USE-method analysis on resource_snapshot.csv; flags CPU/memory saturation, disk/network pressure; returns structured health dict
- Implemented `agentprof/analysis/questions.py` — generates prioritized diagnostic questions from breakdown + resource_health + ExecutionModel; feeds into LLM planner
- Implemented `agentprof/tools/run_workload_tool.py` — wires target agent + baseline observers + storage; writes events.jsonl + resource_snapshot.csv
- Implemented `targets/langchain_react_agent/agent.py` `run_task()` — invokes LangGraph ReAct agent, returns final answer string
- Added `tests/test_milestone2.py` — 18 tests for resource_health and questions (no LLM/GPU)
- 56/56 tests passing (38 Milestone 1 + 18 Milestone 2)



- Fixed `pyproject.toml` build backend: `setuptools.backends.legacy:build` → `setuptools.build_meta` (resolves `pip install -e` failure)
- Added `configs/machines/nusa100.yaml` — shared Linux server (nusa100), 5× A100-SXM4-80GB, 64 CPU, 1 TiB RAM
- Updated `ENVIRONMENT.md`: replaced `overseas_server` placeholder with `nusa100` (real values), updated machine-specific onboarding steps
- Updated `docs/design/onboarding.md`: current branch → `dev`; branch table aligned with COLLAB.md; machine ref → `nusa100`; git auth section updated for HTTPS+PAT
- Updated `.env.example`: added `AGENTPROF_WORK_DIR` and `GITHUB_PAT` fields
- Exported `requirements.lock.txt` from `agentprof` conda env (Python 3.11.15, 54 packages)
- Verified: 38/38 tests pass on nusa100 (`test_schema`, `test_storage`, `test_validator`, `test_analysis`)



- Moved observer implementations to `agentprof/observers/backends/langchain/`
- Moved planner implementations to `agentprof/planner/backends/llm/` and `backends/rule/`
- Added `agentprof/observers/__init__.py` factory: `get_observer()`, `get_all_baseline_observers()`
- Added `agentprof/planner/__init__.py` factory: `get_planner()`
- Added `agentprof/planner/base.py` — `BasePlanner` ABC (FROZEN)
- Added `configs/backends.yaml` — backend selection config
- Added `baselines/` directory with stubs: langfuse_adapter, opentelemetry_adapter, rule_based_profiler
- Added `experiments/designs/` with ADR-001 (observer interface) and ADR-002 (planner interface)
- Added `experiments/comparisons/README.md` — comparison experiment conventions
- Added `COLLAB.md` — Chinese foolproof collaboration guide (branch naming, daily git, ADR template)
- Added `docs/design/collaboration.md` — English formal collaboration spec for CC
- Updated `AGENTS.md` — ownership tiers, shared server resource constraints (≤1/8 CPU/RAM/GPU), Docker workflow
- Updated `README.md` — collaboration section, baselines/ and experiments/ in structure, Milestone 1 marked complete
- Updated `PROJECT_STATUS.md` — module paths to `backends/langchain/`, baselines stubs, 38 tests passing
- Created `dev` branch as daily integration point; merged `refactor/v0.4-architecture` into `dev`

## 2026-05-20 | feat | Milestone 1 — observers + analysis implemented (38 tests, no LLM/GPU)

- Implemented `agentprof/model/observer_registry.py` — `ObserverRegistry.from_yaml()`
- Implemented `agentprof/observers/backends/langchain/resource_snapshot.py` — psutil background thread + `write_csv()`
- Implemented `agentprof/observers/backends/langchain/tool_events.py` — `wrap_tool()` records start/end/error + duration_ms
- Implemented `agentprof/observers/backends/langchain/llm_client_timing.py` — monkey-patches OpenAI client
- Implemented `agentprof/observers/backends/langchain/semantic_langchain.py` — LangChain BaseCallbackHandler
- Implemented `agentprof/analysis/timeline.py` — `build_timeline()` pairs start/end events → SpanRecords + timeline.csv
- Implemented `agentprof/analysis/breakdown.py` — `compute_breakdown()` leaf-span aggregation, llm/tool/wait split
- Added `tests/test_analysis.py` — 17 tests for timeline, breakdown, ObserverRegistry.from_yaml
- Added `tests/fixtures/sample_events.jsonl` — 14 events simulating slow_001 trace
- All 38 tests pass: test_schema, test_storage, test_validator, test_analysis

---

## 2026-05-19 | refactor | v0.4 architecture — LLM planner + deterministic tools + validator

Per `05_cc_revision_and_architecture_guide.md`:

**New packages:**

- `agentprof/schema/`: split into events.py, spans.py, observations.py, evidence.py
- `agentprof/model/`: execution_model.py (correlation graph only), observer_registry.py
- `agentprof/analysis/`: timeline.py, breakdown.py, resource_health.py, questions.py
- `agentprof/planner/`: llm_planner.py, prompts.py, context_builder.py
- `agentprof/tools/`: run_workload_tool.py, inspect_trace_tool.py, query_observer_tool.py, build_report_tool.py
- `agentprof/report/`: markdown_report.py, summary_json.py

**New files:**

- `agentprof/validator.py`: forbidden action enforcement (implemented)
- `agentprof/executor.py`: ObservationPlan executor (stub)
- `agentprof/storage.py`: event read/write (implemented, replaces storage/ package)
- `agentprof/observers/tool_events.py`: renamed from tool_wrapper, capability-driven
- `agentprof/observers/resource_snapshot.py`: early baseline resource observer

**Removed:**

- `agentprof/schema.py` → split into schema/ package
- `agentprof/policy.py` → replaced by planner/llm_planner.py
- `agentprof/questions.py` → moved to analysis/questions.py
- `agentprof/timeline.py` → moved to analysis/timeline.py
- `agentprof/report.py` → moved to report/ package
- `agentprof/observers/tool_wrapper.py` → renamed to tool_events.py
- `agentprof/storage/` package → replaced by storage.py

**Updated:**

- `agentprof/state.py`: added observer_registry, execution_model, resource_health, observation_plans, evidence, action_log, budget_used
- `agentprof/controller.py`: updated docstring for v0.4 loop
- `configs/profiling_spec.yaml`: added forbidden_actions, initial_baseline
- `configs/observers.yaml`: added capabilities, mode, supports_time_window, supports_span_scope fields
- `AGENTS.md`: updated rules for v0.4
- `PROJECT_STATUS.md`: updated status

---

## 2026-05-14 | chore | Repository skeleton initialized

- Created full directory structure
- Wrote all required docs and configs
- Wrote Python package stubs (v0.1 architecture)
- Wrote controlled tools (slow/cpu/flaky) and target agent stub
- Wrote scripts: start_vllm, run_controlled_workload, verify_env
- Design doc and first weekly report
- Git initialized, remote: `git@github.com:NO1xes/AgentProf.git`
