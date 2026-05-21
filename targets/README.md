# targets/

Target agents being profiled by AgentProf. These are the systems under observation — they are **not** part of AgentProf itself.

## Structure

| Directory | Agent | Framework | Status |
| --- | --- | --- | --- |
| `langchain_react_agent/` | LangChain ReAct single agent | LangChain + vLLM | tools implemented; agent stub (Milestone 2) |

## Design principle

Target agents must remain strictly separate from AgentProf. AgentProf observes them externally via callbacks, monkey-patches, and wrappers — it does not modify their internal logic.

## Adding a new target

1. Create `targets/<name>/` with `agent.py`, `tools.py`, `__init__.py`, `README.md`
2. Implement `run_task(task_id: str, config: dict) -> dict` in `agent.py`
3. Register the target in `configs/target_system.yaml`
4. Add a corresponding observer backend in `agentprof/observers/backends/<framework>/`
