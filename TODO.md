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
- [ ] Create conda environment `agentprof` (Python 3.11)
- [ ] Merge refactor/v0.4-architecture → main after review

## Milestone 1: Minimal Event Chain

Implement observers and analysis so a single task run produces events.jsonl + breakdown.

- [ ] `ObserverRegistry.from_yaml()` in `agentprof/model/observer_registry.py`
- [ ] `agentprof/observers/semantic_langchain.py` — LangChain callback hooks
- [ ] `agentprof/observers/llm_client_timing.py` — OpenAI client monkey-patch
- [ ] `agentprof/observers/tool_events.py` — wrap_tool (replaces tool_wrapper)
- [ ] `agentprof/observers/resource_snapshot.py` — psutil sampling thread
- [ ] `agentprof/tools/run_workload_tool.py` — run target agent with baseline observers
- [ ] `targets/langchain_react_agent/agent.py` — implement run_task()
- [ ] `agentprof/analysis/timeline.py` — build_timeline() + write_timeline_csv()
- [ ] `agentprof/analysis/breakdown.py` — compute_breakdown() + write_breakdown_json()
- [ ] `agentprof/analysis/resource_health.py` — compute_resource_health()
- [ ] `agentprof/analysis/questions.py` — generate_questions()
- [ ] Smoke test: run slow_tool task, verify profiles/<run_id>/events.jsonl produced
- [ ] Smoke test: verify breakdown.json has non-zero llm_ms and tool_ms

## Milestone 2: Timeline + Report

- [ ] `agentprof/tools/inspect_trace_tool.py`
- [ ] `agentprof/tools/query_observer_tool.py`
- [ ] `agentprof/tools/build_report_tool.py`
- [ ] `agentprof/executor.py` — execute approved ObservationPlan
- [ ] `agentprof/report/markdown_report.py` — write_markdown_report()
- [ ] `agentprof/report/summary_json.py` — write_summary_json()
- [ ] Run all three controlled tasks end-to-end
- [ ] Review first report.md for correctness

## Milestone 3: LLM Planner + Full Controller Loop

- [ ] `agentprof/planner/context_builder.py` — build_planner_context()
- [ ] `agentprof/planner/llm_planner.py` — plan_observation() with LLM call
- [ ] `agentprof/controller.py` — full run_profiling() loop
- [ ] End-to-end test: controller runs, LLM generates ObservationPlan, validator approves, report produced

## Milestone 4: Multi-Program Workload

- [ ] Extend `configs/workload_controlled.yaml` for multiple programs
- [ ] System aggregation in `agentprof/analysis/breakdown.py`

## Milestone 5: Real Benchmark Subset

- [ ] Select BFCL V3 multi-turn subset
- [ ] Implement trace adapter for BFCL tasks
- [ ] Compare report vs controlled workload

## Deferred / Future

- [ ] `agentprof/observers/vllm_metrics.py` (requires local vLLM, GPU server only)
- [ ] `agentprof/observers/tool_process.py` (psutil process tree, deeper tool attribution)
- [ ] OpenInference / OpenAI Agents SDK adapter
- [ ] Docker setup
