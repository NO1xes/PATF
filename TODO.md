# TODO

## Milestone 0: Repository Skeleton ✅

- [x] Create directory structure
- [x] Write README.md, AGENTS.md, PROJECT_STATUS.md, TODO.md, CHANGELOG.md
- [x] Write ENVIRONMENT.md, SECURITY.md, EXPERIMENTS.md
- [x] Write configs: profiling_spec, target_system, observers, workload_controlled, machines/local_pc_win11
- [x] Write Python package stubs (v0.4 architecture)
- [x] Write controlled tools: slow_tool, cpu_tool, flaky_tool
- [x] Write target agent stub (LangGraph ReAct)
- [x] Write scripts: start_vllm.sh, run_controlled_workload.sh, verify_env.sh
- [x] Initial commit and push to GitHub (commit 8323a7a on main)
- [x] v0.4 architecture refactor pushed to branch refactor/v0.4-architecture
- [x] Create conda environment `agentprof` (Python 3.11) — at E:\conda\envs\agentprof on local_pc_win11
- [x] Merge refactor/v0.4-architecture → dev (done: commit 636162e)

## Milestone 1: Observers + Analysis ✅

Implement observers and analysis so a single task run produces events.jsonl + breakdown.
All items below are testable without LLM/GPU. 38 tests passing.

- [x] `ObserverRegistry.from_yaml()` in `agentprof/model/observer_registry.py`
- [x] `agentprof/observers/backends/langchain/semantic_langchain.py` — LangChain callback hooks
- [x] `agentprof/observers/backends/langchain/llm_client_timing.py` — OpenAI client monkey-patch
- [x] `agentprof/observers/backends/langchain/tool_events.py` — wrap_tool()
- [x] `agentprof/observers/backends/langchain/resource_snapshot.py` — psutil sampling thread
- [x] `agentprof/analysis/timeline.py` — build_timeline() + write_timeline_csv()
- [x] `agentprof/analysis/breakdown.py` — compute_breakdown() + write_breakdown_json()
- [x] `agentprof/observers/__init__.py` — factory: get_observer(), get_all_baseline_observers()
- [x] `agentprof/planner/base.py` — BasePlanner ABC (FROZEN)
- [x] `agentprof/planner/__init__.py` — factory: get_planner()
- [x] Collaboration structure: backends/ layout, COLLAB.md, docs/design/collaboration.md, ADRs
- [x] `agentprof/observers/backends/langchain/semantic_langchain.py` — runtime test (smoke test passed 2026-05-23)
- [x] `targets/langchain_react_agent/agent.py` — implement run_task() (tested via smoke test 2026-05-23)

## Milestone 2: resource_health + questions + run_workload ✅

- [x] `agentprof/analysis/resource_health.py` — USE method on resource_snapshot.csv
- [x] `agentprof/analysis/questions.py` — generate diagnostic questions from breakdown + resource_health
- [x] `agentprof/tools/run_workload_tool.py` — run target agent, collect events.jsonl
- [x] `targets/langchain_react_agent/agent.py` — implement `run_task()`
- [x] `agentprof/planner/backends/rule/rule_planner.py` — rule-based planner (ablation baseline b)
- [x] End-to-end smoke test: run slow_001/cpu_001/flaky_001 → events.jsonl → timeline.csv → breakdown.json
- [x] Smoke test: verified breakdown.json has non-zero llm_ms (34.8%) and tool_ms (65.2%)

## Milestone 3: LLM Planner + Full Controller Loop ✅

- [x] `agentprof/planner/backends/llm/context_builder.py` — build_planner_context()
- [x] `agentprof/planner/backends/llm/llm_planner.py` — plan_observation() with LLM call
- [x] `agentprof/executor.py` — execute approved ObservationPlan
- [x] `agentprof/controller.py` — full run_profiling() loop
- [x] End-to-end test: controller runs, rule planner generates ObservationPlan, validator approves, report.md produced (2026-05-23)
- [x] LLM planner smoke test: verify Qwen3 LLM generates valid ObservationPlan JSON (AGENTPROF_PLANNER=llm)

## Milestone 4: Report Quality + Multi-Program Workload

- [x] `agentprof/report/markdown_report.py` — write_markdown_report()
- [x] `agentprof/report/summary_json.py` — write_summary_json()
- [x] Run all three controlled tasks end-to-end (slow_001, cpu_001, flaky_001 — smoke test 2026-05-23)
- [x] Review first report.md for correctness (profiles/run_c9ef5986/report.md reviewed)
- [x] `configs/workload_controlled.yaml` — verify multi-program config is complete
- [x] System-level aggregation across programs in `agentprof/analysis/breakdown.py`

## Milestone 5: Real Benchmark Subset

- [ ] **NO1xes:** select BFCL V3 multi-turn subset for demo-scale evaluation
- [ ] **NO1xes:** run target agent with vLLM on the selected subset; keep AgentProf planner free to use a separate API endpoint when needed to avoid local vLLM contention
- [ ] **NO1xes:** implement the minimum BFCL trace adapter needed for AgentProf inputs
- [ ] **NO1xes:** compare report vs controlled workload and identify what changes from toy tasks to real benchmark traces
- [ ] **collab:** add fixture-only tests for BFCL adapter parsing and malformed-trace handling
- [ ] **collab:** document BFCL subset selection criteria and reproduction notes in `experiments/comparisons/`

## Test Roadmap

Tests must evolve with new features. Add tests before or alongside each feature; keep Tier 1 tests GPU-free and API-free.

- [x] Add report snapshot/structure tests for `report.md` and `summary.json` multi-program sections
- [x] Add controller dry-run tests that use fixture events and rule planner without vLLM
- [ ] Add BFCL adapter fixture tests before running BFCL experiments
- [ ] Add baseline adapter fixture tests for Langfuse/OpenTelemetry/Phoenix-style traces
- [ ] Add resource-limit guard tests or script checks for Docker/Tier 3 command templates
- [ ] Maintain a small golden `profiles/`-like fixture under `tests/fixtures/` for regression tests, without committing large logs

## Baselines (parallel track, no milestone dependency)

- [ ] **collab:** survey GitHub/open-source agent observability and profiling tools for qualitative baselines; search `agentprof`, `agent profiler`, `LLM agent profiling`, `agent observability`, and `OpenTelemetry agent tracing`; explicitly discard unrelated "agent profile" hits
- [ ] **collab:** shortlist candidate baselines with fit notes; initial candidates include Langfuse, Arize Phoenix/OpenInference, AgentOps, AgentSight, OpenTelemetry-native stacks, and any relevant AgentProf-named project found during survey
- [ ] **collab:** `baselines/langfuse_adapter/` — wrap Langfuse/OpenTelemetry-style output → AgentEvent format (baseline a)
- [ ] **collab:** `baselines/opentelemetry_adapter/` — wrap raw OTel/OpenInference spans → AgentEvent format (baseline a)
- [ ] **collab:** create `experiments/comparisons/exp003-agentprof-vs-observability-baselines/` for motivation-style comparison, not strict variable-control evaluation
- [ ] **NO1xes:** `baselines/rule_based_profiler/` — standalone rule-based profiler (ablation baseline b)
- [ ] **NO1xes:** run demo comparison: AgentProf vs selected baseline(s), focusing on observed strengths, weaknesses, and potential improvements

## Deferred / Future

- [ ] `agentprof/observers/vllm_metrics.py` (requires local vLLM, GPU server only)
- [ ] `agentprof/observers/tool_process.py` (psutil process tree, deeper tool attribution)
- [ ] OpenInference / OpenAI Agents SDK adapter
- [ ] Docker setup for Tier 3 experiments
