#!/usr/bin/env bash
# Push over HTTPS using GITHUB_USER and GITHUB_PAT from .env without placing
# the token in the remote URL, shell history, or git config.

set -euo pipefail

if [[ ! -f ".env" ]]; then
    echo "ERROR: .env not found. Run from repo root."
    exit 1
fi

set -a
# shellcheck disable=SC1091
source ".env"
set +a

if [[ -z "${GITHUB_USER:-}" || -z "${GITHUB_PAT:-}" ]]; then
    echo "ERROR: GITHUB_USER and GITHUB_PAT must be set in .env."
    exit 1
fi

ASKPASS="$(mktemp ".git/agentprof-git-askpass.XXXXXX")"
chmod 700 "$ASKPASS"
cleanup() {
    rm -f "$ASKPASS"
}
trap cleanup EXIT

cat >"$ASKPASS" <<'EOF'
#!/usr/bin/env bash
case "$1" in
    *Username*) printf '%s\n' "$GITHUB_USER" ;;
    *Password*) printf '%s\n' "$GITHUB_PAT" ;;
    *) printf '\n' ;;
esac
EOF
chmod 700 "$ASKPASS"

GIT_ASKPASS="$ASKPASS" GIT_TERMINAL_PROMPT=0 git push "$@"
