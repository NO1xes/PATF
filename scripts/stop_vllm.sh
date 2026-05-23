#!/usr/bin/env bash
# Stop the vLLM server started by start_vllm.sh.
# Kills the main process AND all child processes (worker subprocesses).
#
# Usage:
#   bash scripts/stop_vllm.sh          # uses vllm.pid
#   bash scripts/stop_vllm.sh 18796    # find by port if vllm.pid missing

set -euo pipefail

PORT="${1:-}"

find_pid_by_port() {
    ss -tlnp 2>/dev/null | grep ":${1} " | grep -oP 'pid=\K[0-9]+' | head -1
}

if [[ -f vllm.pid ]]; then
    MAIN_PID=$(cat vllm.pid)
else
    if [[ -z "$PORT" ]]; then
        echo "[stop_vllm] No vllm.pid found. Pass a port: bash scripts/stop_vllm.sh <port>"
        exit 1
    fi
    MAIN_PID=$(find_pid_by_port "$PORT")
    if [[ -z "$MAIN_PID" ]]; then
        # fall back: search by process name
        MAIN_PID=$(pgrep -f "vllm.entrypoints.openai.api_server" | head -1 || true)
    fi
fi

if [[ -z "$MAIN_PID" ]]; then
    echo "[stop_vllm] Could not find vLLM process."
    exit 1
fi

echo "[stop_vllm] Main PID: $MAIN_PID"

# Kill the entire process group rooted at MAIN_PID
# pgrep -P finds direct children; pkill -P kills them recursively
echo "[stop_vllm] Killing process tree..."
kill -9 "$MAIN_PID" 2>/dev/null || true
# Also kill any remaining VLLM worker processes (they may have re-parented)
pkill -9 -f "VLLM::Worker" 2>/dev/null || true
pkill -9 -f "VLLM::EngineCore" 2>/dev/null || true

sleep 2

# Verify GPU memory released
echo "[stop_vllm] Checking GPU memory..."
nvidia-smi --query-gpu=index,memory.used --format=csv,noheader 2>/dev/null | awk -F', ' '{used=$2+0; if(used>100) print "  GPU "$1": "$2" still in use (may take a few seconds)"}'

[[ -f vllm.pid ]] && rm vllm.pid && echo "[stop_vllm] Removed vllm.pid"
echo "[stop_vllm] Done."
