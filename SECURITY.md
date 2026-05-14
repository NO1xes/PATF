# Security Notes

## Keys and Secrets

- **Never commit `.env`** — it contains API keys and tokens.
- `.env.example` is the only committed template; it contains no real values.
- If a key is accidentally committed: rotate it immediately, then remove from git history.
- Model weights (`.pt`, `.safetensors`, `.gguf`) must not be committed — they are large and may be licensed.

## Personal Machine (local_pc_win11)

- Single user, no shared access concerns.
- SSH key for GitHub is user-scoped — no special precautions needed beyond keeping the private key secure.
- `git config --global` is safe to use.

## Shared / GPU Servers (future)

When working on a shared machine:

- Use `git config --local` (not `--global`) to set user.name and user.email per-repo.
- Do not use default port 8000 for vLLM if others share the machine — set a custom port in `configs/machines/<name>.yaml`.
- Do not install system packages without permission.
- Use conda env or Docker to isolate the environment.
- Output only to the project workspace directory — never write to `/tmp` or shared paths.
- If using Docker: do not run as root unless vLLM/GPU requires it; use a named user.
- Coding agents (Claude Code, Codex) must not have permission to delete system directories or write outside the project workspace.

## API Keys in Use

| Key | Where stored | Used for |
|---|---|---|
| `OPENAI_API_KEY` or `VLLM_API_KEY` | `.env` | LLM backend calls |
| GitHub SSH key | `~/.ssh/` | git push/pull |

## Coding Agent Permissions

Coding agents should only be able to:
- Read/write files within the project workspace
- Run `python`, `pytest`, `pip install` within the conda env
- Run scripts in `scripts/`

Coding agents must NOT:
- Run `rm -rf` outside the project workspace
- Modify system config or install system packages
- Access or print the contents of `.env`
- Push to `main` directly — always use a branch
