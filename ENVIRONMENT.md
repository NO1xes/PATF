# Environment Setup

This document tells you how to set up the environment on any machine.
**Read this first when onboarding a new machine.**

---

## Registered Machines

| machine_id | OS | GPU | Role | Config file |
|---|---|---|---|---|
| local_pc_win11 | Windows 11 Home (China) | None | API experiments, dev | `configs/machines/local_pc_win11.yaml` |
| _(gpu_server)_ | TBD | TBD | vLLM backend, large-scale runs | `configs/machines/<name>.yaml` (add when available) |

---

## General Setup (All Machines)

### 1. Clone the repo

**SSH (preferred, works on machines with SSH key configured):**
```bash
git clone git@github.com:NO1xes/AgentProf.git
```

**HTTPS (fallback, e.g. machines where SSH is blocked or key not set up):**
```bash
git clone https://github.com/NO1xes/AgentProf.git
```

> On shared servers in China: SSH to GitHub usually works. If not, use HTTPS with a personal access token (PAT) — store the PAT in `.env`, never hardcode it.

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
