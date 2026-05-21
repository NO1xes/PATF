# scripts/

Shell scripts for starting services, running workloads, and verifying the environment.

## Files

| Script | Purpose |
| --- | --- |
| `verify_env.sh` | Check conda env, Python version, required packages, `.env` variables |
| `start_vllm.sh` | Start vLLM server with Qwen3-30B-A3B (GPU server only) |
| `run_controlled_workload.sh` | Run the controlled workload end-to-end and produce a profile |

## Usage

```bash
# 1. Verify environment before any work
bash scripts/verify_env.sh

# 2. Start vLLM backend (GPU server only)
bash scripts/start_vllm.sh

# 3. Run controlled workload (requires LLM endpoint in .env)
bash scripts/run_controlled_workload.sh
```

## Tier constraints

| Tier | Script | Where to run |
| --- | --- | --- |
| Tier 1 | `verify_env.sh` | Any machine, conda env |
| Tier 2 | `run_controlled_workload.sh` | Local or overseas server, enforce `ulimit` |
| Tier 3 | `start_vllm.sh` + full workload | GPU server only, via Docker or SLURM |

See `AGENTS.md` for shared server resource limits (≤1/8 CPU/RAM/GPU).
