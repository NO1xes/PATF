# ADR-001: Observer Interface Design

- **Date**: 2026-05-21
- **Status**: Accepted
- **Deciders**: NO1xes (lead)

## Context

AgentProf needs to collect events from four execution layers. Early versions
had observer implementations directly in `agentprof/observers/`. As the project
moves toward comparing multiple frameworks (LangChain vs DeepAgent) and enabling
two collaborators to develop independent implementations, a stable interface is needed.

## Decision

Adopt the **Interface + Backend** pattern:

- `agentprof/observers/base.py` — `BaseObserver` ABC, frozen (no single-party changes)
- `agentprof/observers/backends/<name>/` — concrete implementations, one per framework
- `agentprof/observers/__init__.py` — `get_observer(name, run_id)` factory, reads `AGENTPROF_BACKEND`

## Options Considered

### Option A: Keep all implementations flat in `agentprof/observers/`
- Pro: Simple, no factory indirection
- Con: Cannot have two implementations of the same observer coexist;
  switching frameworks requires editing core files

### Option B: Interface + Backend (chosen)
- Pro: `base.py` and factory contract are stable; each framework lives in isolation;
  switching backend is one env var change; two collaborators can each own a backend
- Con: One extra level of indirection; factory must be kept in sync with backends

### Option C: Plugin registry (entry_points)
- Pro: Most extensible, supports third-party backends
- Con: Overkill for a two-person research project; adds packaging complexity

## Consequences

- `semantic_langchain`, `llm_client_timing`, `tool_events`, `resource_snapshot` moved to
  `agentprof/observers/backends/langchain/`
- Future DeepAgent backend goes in `agentprof/observers/backends/deepagent/`
- All existing tests remain valid; only import paths changed
- `AGENTPROF_BACKEND=langchain` in `.env` selects the backend

## Reverting

If the backend pattern proves too heavy, flatten by copying files from
`backends/langchain/` back to `observers/` and reverting `__init__.py`.
No schema or test changes required.
