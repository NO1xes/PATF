# Environment Setup

This document tells you how to set up the environment on any machine.
**Read this first when onboarding a new machine.**

---

## Registered Machines

| machine_id | OS | GPU | Role | Shared | Config file |
| --- | --- | --- | --- | --- | --- |
| local_pc_win11 | Windows 11 Home (China) | None | API experiments, dev | No | `configs/machines/local_pc_win11.yaml` |
| overseas_server | TBD (Linux) | TBD | LangChain tests, vLLM backend | Yes | `configs/machines/overseas_server.yaml` (add when confirmed) |

---

## General Setup (All Machines)

### 1. Clone the repo

**SSH (preferred, works on machines with SSH key configured):**
```bash
git clone git@github.com:NO1xes/AgentProf.git
```

**HTTPS + Personal Access Token (PAT) — for shared servers where SSH is not set up:**

```bash
# Replace <PAT> with your GitHub Personal Access Token
git clone https://<PAT>@github.com/NO1xes/AgentProf.git
```

How to get a PAT: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → New token. Grant `Contents: Read and Write` on the AgentProf repo.

Store the PAT in `.env` as `GITHUB_PAT=<token>` — never hardcode it in scripts or commit it.

On a shared server, set git identity locally (not globally, to avoid polluting other users):

```bash
git config --local user.name "your-github-handle"
git config --local user.email "your@email.com"
```

> SSH is preferred on personal machines. Use HTTPS+PAT on shared servers where you cannot install SSH keys.

### 2. Create conda environment

```bash
conda create -n agentprof python=3.11 -y
conda activate agentprof
pip install -e ".[dev]"
```

> Python 3.11 is recommended for compatibility with LangChain and vLLM. The local PC currently runs 3.13 — if dependency issues arise, create the env with 3.11 explicitly.

### 3. Copy and fill environment variables

```bash
cp .env.example .env
# Edit .env with your actual values
```

### 4. Verify setup

```bash
python -c "import langchain; print(langchain.__version__)"
python -m pytest tests/ -x -q  # once tests exist
```

---

## Machine-Specific Notes

### overseas_server (shared Linux server, GPU available)

This is a shared machine. Follow all resource constraints in `AGENTS.md` before running anything.

**Onboarding steps:**

```bash
# 1. Clone with HTTPS+PAT (SSH likely not available)
git clone https://<PAT>@github.com/NO1xes/AgentProf.git
cd AgentProf
git checkout dev

# 2. Set git identity locally (never --global on shared servers)
git config --local user.name "your-github-handle"
git config --local user.email "your@email.com"

# 3. Create conda env in your own prefix (not base)
conda create -n agentprof python=3.11 -y
conda activate agentprof

# 4. Install dependencies
pip install -e ".[dev]"
# If slow, try a mirror: pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. Copy and fill .env
cp .env.example .env
# Required fields:
#   VLLM_BASE_URL=http://localhost:8000/v1   (or remote endpoint)
#   AGENTPROF_MACHINE=overseas_server
#   AGENTPROF_WORK_DIR=/path/to/your/workdir  (must be under your quota)

# 6. Verify (Tier 1 — no GPU, no LLM needed)
bash scripts/verify_env.sh
pytest tests/test_schema.py tests/test_storage.py tests/test_validator.py tests/test_analysis.py -v
```

**Resource limits (enforce before any run):**

```bash
# Check available resources first
nproc          # total CPU cores — use at most 1/8
free -h        # total RAM — use at most 1/8
nvidia-smi     # GPU memory — use at most 1/8 per GPU

# Enforce CPU/RAM limits for Tier 2 runs
ulimit -u 32                    # max 32 child processes
# Use taskset or Docker for CPU pinning (see AGENTS.md)
```

**Do NOT:**

- `pip install` or `conda install` into base environment
- Write output outside `$AGENTPROF_WORK_DIR`
- Run `pytest` without `-x` on login node — submit via job scheduler
- Leave zombie processes — always call `observer.detach()` and clean up

See `AGENTS.md` "Shared Server Resource Constraints" for the full rules.

### local_pc_win11 (Windows 11, China mainland, no GPU)

- conda base: `E:\miniconda3`
- Git auth: SSH (`git@github.com`), confirmed working
- Network: China mainland — use pip mirror and HuggingFace mirror (see below)
- Role: API-based experiments only. vLLM does NOT run here.
- Workspace: `d:/JediXing/Documents/HUST/class/26spring/Multiagent/agent4profiling/stage1-knowledge/2026-05-13/agentprof`

**pip mirror (Tsinghua, recommended in China):**
```bash
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple
```
Or set permanently:
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**HuggingFace mirror:**
```bash
# Add to .env:
HF_ENDPOINT=https://hf-mirror.com
```

---

## Adding a New Machine

1. Run the experiment on the new machine and note: OS, GPU, Python version, conda/venv path, git auth method, network environment, shared/personal.
2. Copy `configs/machines/local_pc_win11.yaml` as a template.
3. Fill in the new machine's values.
4. Add a row to the table above.
5. Commit the new machine config file.

---

## Version Pinning

Key versions are declared in `pyproject.toml`. After installing, freeze with:
```bash
pip freeze > requirements.lock.txt
```
Commit `requirements.lock.txt` for reproducibility on GPU servers.
