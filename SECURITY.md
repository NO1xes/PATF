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
- Keep GitHub remotes as plain HTTPS or SSH URLs; never embed PATs in remote URLs.
- For HTTPS git push, store `GITHUB_USER` and `GITHUB_PAT` in `.env` and use `scripts/git_push_with_env_pat.sh`.
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
| `GITHUB_USER`, `GITHUB_PAT` | `.env` | HTTPS git push/pull on shared servers |
| GitHub SSH key | `~/.ssh/` | git push/pull |

## Coding Agent Permissions

Coding agents should only be able to:
- Read/write files within the project workspace
- Run `python`, `pytest`, `pip install` within the conda env
- Run scripts in `scripts/`

Coding agents must NOT:
- Run `rm -rf` outside the project workspace
- Modify system config or install system packages
- Print, summarize, commit, or persist the contents of `.env`
- Put secrets in command arguments, git remote URLs, shell history, docs, commits, or chat
- Push to `main` directly — always use a branch

Coding agents MAY load `.env` inside a local command when needed for an approved action, such as running a script that passes credentials to git without printing them.
