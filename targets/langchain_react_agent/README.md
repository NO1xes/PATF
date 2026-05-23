# targets/langchain_react_agent/

The target agent being profiled by AgentProf. This is a LangChain ReAct single agent with three controlled tools designed to produce measurable latency signals.

**This is NOT part of AgentProf.** It is the system under observation.

## Files

| File | Purpose |
| --- | --- |
| `tools.py` | Three controlled tools: `slow_tool`, `cpu_tool`, `flaky_tool` |
| `agent.py` | LangChain ReAct agent — `run_task(task_id, config)` entry point (stub, Milestone 2) |
| `__init__.py` | Package init |

## Tools

| Tool | Behavior | Profiling signal |
| --- | --- | --- |
| `slow_tool` | `time.sleep(N)` | Pure wait latency |
| `cpu_tool` | Busy loop for N seconds | CPU-bound tool latency |
| `flaky_tool` | Fails with probability p, retries | Retry overhead, error events |

## Runtime requirements

- `langchain` and `langchain-openai` (not installed on local_pc_win11 — use overseas server)
- vLLM endpoint set in `.env` as `VLLM_BASE_URL`

## Status

- `tools.py` — implemented, tested via `tests/test_tools.py` (needs langchain at runtime)
- `agent.py` — stub, `run_task()` raises `NotImplementedError` (Milestone 2)
