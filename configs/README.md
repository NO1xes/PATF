# configs/

All configuration files for AgentProf. No hardcoded paths or values in code — everything reads from here or `.env`.

## Files

| File | Purpose |
| --- | --- |
| `profiling_spec.yaml` | Profiling campaign spec: target, observers, budget, `forbidden_actions` |
| `target_system.yaml` | Target agent description: framework, entry point, tool list |
| `observers.yaml` | Observer capability registry: name, layer, capabilities, mode |
| `backends.yaml` | Backend selection: `observer_backend`, `planner_backend` |
| `workload_controlled.yaml` | Controlled workload definition: tasks, repetitions, arrival rate |
| `machines/<id>.yaml` | Per-machine environment: OS, GPU, conda path, network, git auth |

## Backend switching

To switch observer or planner backend without changing code, edit `.env`:

```bash
AGENTPROF_BACKEND=langchain   # observer backend
AGENTPROF_PLANNER=llm         # planner backend (llm | rule)
```

Or override per-run:

```bash
AGENTPROF_PLANNER=rule python -m agentprof.runner ...
```

## Adding a new machine

1. Copy `machines/local_pc_win11.yaml` → `machines/<new_id>.yaml`
2. Fill in all fields (OS, GPU, conda path, network, git auth method)
3. Add a row to the machine table in `ENVIRONMENT.md`
4. Commit: `git add configs/machines/ ENVIRONMENT.md`
