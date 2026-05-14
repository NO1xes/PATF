# Project Status

Last updated: 2026-05-14

## Current Milestone

**Milestone 0: Repository Skeleton** — IN PROGRESS

## Completed

- [x] Project design documents written (see `2026-05-13/agentprof_docs/`)
- [x] Local project directory created at `stage1-knowledge/2026-05-13/agentprof/`
- [x] Git initialized, remote set to `git@github.com:NO1xes/AgentProf.git`
- [x] `README.md`, `AGENTS.md` written
- [x] Directory structure created (agentprof/, targets/, configs/, scripts/, experiments/, docs/, docker/, profiles/)

## In Progress

- [ ] Writing all skeleton files (docs, configs, Python stubs, scripts)
- [ ] Initial commit and push to GitHub

## Blocked / Pending

- [ ] **vLLM backend**: requires GPU server (not available on local PC). Local PC is for API-based experiments only.
- [ ] Conda environment creation: pending `pyproject.toml` finalization
- [ ] Target agent smoke test: pending environment setup

## Next Steps (Milestone 1)

1. Create conda env and install dependencies
2. Verify OpenAI-compatible API call works (against remote API or local vLLM on server)
3. Implement `agentprof/observers/semantic_langchain.py`
4. Implement `agentprof/observers/llm_client_timing.py`
5. Implement `agentprof/observers/tool_wrapper.py`
6. Run slow/cpu/flaky tasks and produce first `events.jsonl`

## Architecture Snapshot

```
Target Agent    = LangChain/LangGraph ReAct single agent
LLM Backend     = vLLM OpenAI-compatible server (on GPU server, not local PC)
AgentProf       = external profiling controller
```

## Known Unknowns

- Which GPU server will be used for vLLM? (TBD — another team member handles this)
- Which model? Currently configured as `Qwen/Qwen2.5-7B-Instruct` in `configs/target_system.yaml`
- BFCL V3 subset selection criteria (deferred to MVP-2)
