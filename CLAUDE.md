# AgentProf — Claude Code Instructions

## Project in One Line
Methodology-driven profiling controller for LLM agent systems. **Profiling only — zero optimization.**

## Current State (as of 2026-05-23)
- Branch: `dev` (working branch; PRs target `dev`, not `main`)
- All Milestones 0–3 implemented; 56/56 tests passing
- Pending: live end-to-end smoke test (needs vLLM)
- See `PROJECT_STATUS.md` for module-level status, `TODO.md` for task list

## Machine: nusa100 (this machine)
- Hostname: `xtraa100`, shared server
- 8× A100-SXM4-80GB; **use at most 2 GPUs** (CUDA_VISIBLE_DEVICES=1,6 are currently free)
- 64 CPU cores; use ≤ 8
- conda env: `agentprof` at `/disk2/runyuan/envs/agentprof`
- vLLM env: `vllm` at `/disk2/runyuan/envs/vllm` (vllm 0.15.1)
- Model cache: `/disk2/runyuan/home_links/cache/huggingface/hub/models--Qwen--Qwen3-30B-A3B-Instruct-2507`
- Model name to use: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- git auth: HTTPS + PAT (stored in `.env` as `GITHUB_PAT`)
- Workspace: `/disk2/runyuan/projects/AgentProf`

## Hard Constraints (from AGENTS.md)
- **NEVER** implement forbidden actions: change_concurrency, change_arrival_rate, toggle_cache, set_timeout, set_quota, apply_patch, modify_prompt, modify_planner
- **NEVER** modify FROZEN modules' interfaces: `schema/`, `model/`, `validator.py`, `storage.py`, `state.py`, `observers/base.py`, `planner/base.py`
- **NEVER** commit `.env`, API keys, model weights, large logs
- All output goes to `profiles/<run_id>/`
- Use `git config --local` only (never `--global`)
- Do not install into base conda env

## vLLM on This Server
- Use **CUDA_VISIBLE_DEVICES=1** (single card; GPU 1 is currently free)
- Use port **18796** (confirmed unused; occupied range is 18789–18793)
- Start: `bash scripts/start_vllm.sh 18796 bg 1`
- Stop: `bash scripts/stop_vllm.sh`
- Metrics endpoint: `GET http://localhost:<port>/metrics` (Prometheus, built into vLLM)
- AgentProf connects via `VLLM_BASE_URL=http://localhost:18796/v1` in `.env`
- **Always run stop_vllm.sh after use** — GPU memory is not released until all child processes die
- gpu-memory-utilization: 0.90 (model weights ~60 GB fp16; needs ~72 GB of 80 GB)

## Key Files (read order for new session)
1. `README.md` → `AGENTS.md` → `PROJECT_STATUS.md` → `TODO.md`
2. `docs/design/onboarding.md` for module map
3. `CHANGELOG.md` for recent changes

## After Any Code Change
- Update `CHANGELOG.md` (append one line)
- Update `PROJECT_STATUS.md` if module status changes
- Update `TODO.md` if task status changes
- Run `pytest tests/ -x -q` before committing
