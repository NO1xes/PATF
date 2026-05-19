# Changelog

All notable changes to AgentProf are recorded here.
Format: `YYYY-MM-DD | type | description`
Types: `feat` / `fix` / `docs` / `exp` / `refactor` / `chore`

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
