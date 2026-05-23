#!/usr/bin/env bash
# Start vLLM with Qwen3-30B-A3B-Instruct-2507 in OpenAI-compatible mode.
# Run on nusa100 only. Uses GPU 1 and 6 (free as of 2026-05-23; verify first).
#
# Usage:
#   bash scripts/start_vllm.sh            # foreground, port 18796
#   bash scripts/start_vllm.sh 18797      # custom port
#   bash scripts/start_vllm.sh 18796 bg   # background, PID saved to vllm.pid
#
# Monitor:
#   curl -s http://localhost:18796/health
#   curl -s http://localhost:18796/metrics | grep vllm:
#   nvidia-smi -i 1,6 --query-gpu=memory.used,utilization.gpu --format=csv -l 5
#
# Stop:
#   kill $(cat vllm.pid)   # if started in background
#   or Ctrl-C              # if foreground

set -euo pipefail

PORT="${1:-18796}"
BG="${2:-}"
MODEL_ID="Qwen/Qwen3-30B-A3B-Instruct-2507"
HF_HOME_PATH="/disk2/runyuan/home_links/cache/huggingface"

echo "[vllm] Checking GPU availability..."
nvidia-smi -i 1,6 --query-gpu=index,memory.used,memory.free --format=csv,noheader
echo ""

echo "[vllm] Starting $MODEL_ID on port $PORT (GPUs 1,6) ..."

CMD=(
  conda run -n vllm
  env
    CUDA_VISIBLE_DEVICES=1,6
    HF_HOME="$HF_HOME_PATH"
  python -m vllm.entrypoints.openai.api_server
    --model "$MODEL_ID"
    --port "$PORT"
    --host 127.0.0.1
    --trust-remote-code
    --tensor-parallel-size 2
    --gpu-memory-utilization 0.50
    --max-model-len 8192
    --enable-prefix-caching
    --disable-log-requests
)

if [[ "$BG" == "bg" ]]; then
    "${CMD[@]}" > logs/vllm_${PORT}.log 2>&1 &
    echo $! > vllm.pid
    echo "[vllm] Started in background. PID=$(cat vllm.pid)"
    echo "[vllm] Logs: logs/vllm_${PORT}.log"
    echo "[vllm] Health check: curl http://localhost:${PORT}/health"
    echo "[vllm] Stop: kill \$(cat vllm.pid)"
else
    "${CMD[@]}"
fi
