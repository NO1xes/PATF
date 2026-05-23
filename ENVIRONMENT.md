# Environment Setup

This document tells you how to set up the environment on any machine.
**Read this first when onboarding a new machine.**

---

## Registered Machines

| machine_id | OS | GPU | Role | Shared | Config file |
| --- | --- | --- | --- | --- | --- |
| local_pc_win11 | Windows 11 Home (China) | None | API experiments, dev | No | `configs/machines/local_pc_win11.yaml` |
| nusa100 | Ubuntu Linux | 5× A100-SXM4-80GB | LangChain tests, vLLM backend | Yes | `configs/machines/nusa100.yaml` |

---

## General Setup (All Machines)

### 1. Clone the repo

**SSH (preferred, works on machines with SSH key configured):**
```bash
git clone git@github.com:NO1xes/PATF.git
```

**HTTPS + Personal Access Token (PAT) — for shared servers where SSH is not set up:**

```bash
# Replace <PAT> with your GitHub Personal Access Token
git clone https://<PAT>@github.com/NO1xes/PATF.git
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

> Python 3.11 is recommended for compatibility with LangChain and vLLM.

### 3. Copy and fill environment variables

```bash
cp .env.example .env
# Edit .env with your actual values
```

Key fields (see `.env.example` for full list):
- `VLLM_BASE_URL`, `VLLM_MODEL` — LLM backend endpoint
- `VLLM_PYTHON`, `HF_HOME` — GPU server only; paths to vllm env and HF cache
- `AGENTPROF_MACHINE` — machine_id (e.g. `nusa100`, `local_pc_win11`)
- `AGENTPROF_WORK_DIR` — your local workspace root
- `GITHUB_PAT` — for git push on shared servers (never commit)

### 4. Verify setup

```bash
conda activate agentprof
pytest tests/ -x -q
# 63 tests should pass without GPU or LLM
```

---

## Machine-Specific Notes

### nusa100 (shared Linux server, 5× A100-SXM4-80GB)

This is a shared machine. Follow all resource constraints in `AGENTS.md` before running anything.

**Onboarding steps:**

```bash
# 1. Clone with HTTPS+PAT (no SSH key on shared server)
git clone https://<PAT>@github.com/NO1xes/PATF.git
cd PATF
git checkout dev

# 2. Set git identity locally (never --global on shared servers)
git config --local user.name "your-github-handle"
git config --local user.email "your@email.com"

# 3. Activate conda env (create if not present: conda create -n agentprof python=3.11 -y)
conda activate agentprof

# 4. Install package in editable mode
pip install -e ".[dev]"

# 5. Copy local config template and fill in your paths
cp configs/machines/nusa100.local.yaml.example configs/machines/nusa100.local.yaml
# Edit nusa100.local.yaml with your actual paths (gitignored)

# 6. Copy and fill .env (see .env.example for all fields)
cp .env.example .env
# Required for this machine:
#   VLLM_PYTHON=/your/envs/vllm/bin/python
#   HF_HOME=/your/cache/huggingface
#   VLLM_BASE_URL=http://localhost:<port>/v1
#   AGENTPROF_MACHINE=nusa100
#   AGENTPROF_WORK_DIR=/your/workspace/PATF
#   GITHUB_PAT=<your-token>

# 7. Verify (no GPU needed)
pytest tests/ -x -q
```

**Resource limits (enforce before any run):**

```bash
nproc          # 64 total — use at most 8
free -h        # ~1 TiB total — use at most 128 GiB
nvidia-smi     # 5× A100 80GB — use at most 1 GPU (CUDA_VISIBLE_DEVICES=<id>)
```

**Do NOT:**

- Install into the shared base conda environment
- Write output outside `$AGENTPROF_WORK_DIR`
- Leave zombie processes — always call `stop_vllm.sh` after GPU runs
- Run `pytest` without `-x` on the login node

See `AGENTS.md` "Shared Server Resource Constraints" for the full rules.

### local_pc_win11 (Windows 11, China mainland, no GPU)

- Git auth: SSH (`git@github.com`), confirmed working
- Network: China mainland — use pip mirror and HuggingFace mirror (see below)
- Role: API-based experiments only. vLLM does NOT run here.

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

1. Note: OS, GPU, Python version, git auth method, network, shared/personal.
2. Create `configs/machines/<id>.yaml` (hardware/role only — no private paths).
3. Create `configs/machines/<id>.local.yaml` from the `.example` template (gitignored).
4. Add `.env` entries for `VLLM_PYTHON`, `HF_HOME`, `AGENTPROF_WORK_DIR` etc.
5. Add a row to the Registered Machines table above.
6. Commit only the public `<id>.yaml`; `.local.yaml` and `.env` stay local.

---

## Version Pinning

Key versions are declared in `pyproject.toml`. After installing, freeze with:
```bash
pip freeze > requirements.lock.txt
```
Commit `requirements.lock.txt` for reproducibility on GPU servers.
