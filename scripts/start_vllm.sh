#!/usr/bin/env bash
# Start vLLM with Qwen3-30B-A3B-Instruct-2507 in OpenAI-compatible mode.
# Run on nusa100 only. Default: single GPU (GPU 1), port 18796.
#
# Usage:
#   bash scripts/start_vllm.sh                  # foreground, port 18796, GPU 1
#   bash scripts/start_vllm.sh 18797            # custom port
#   bash scripts/start_vllm.sh 18796 bg         # background, PID saved to vllm.pid
#   bash scripts/start_vllm.sh 18796 bg 6       # use GPU 6 instead
#
# Monitor:
#   tail -f logs/vllm_18796.log                 # startup progress
#   curl -s http://localhost:18796/health        # {"status":"ok"} when ready
#   curl -s http://localhost:18796/metrics | grep -E "^vllm"   # Prometheus metrics
#   nvidia-smi -i 1 --query-gpu=memory.used,utilization.gpu --format=csv -l 5
#
# Stop (GPU does not release until ALL child processes die):
#   kill -9 $(cat vllm.pid) && rm vllm.pid
#   # then verify: nvidia-smi -i 1 --query-gpu=memory.used --format=csv,noheader

set -euo pipefail

PORT="${1:-18796}"
BG="${2:-}"
GPU="${3:-1}"
MODEL_ID="Qwen/Qwen3-30B-A3B-Instruct-2507"
HF_HOME_PATH="/disk2/runyuan/home_links/cache/huggingface"
VLLM_PYTHON="/disk2/runyuan/envs/vllm/bin/python"

echo "[vllm] Checking GPU availability..."
nvidia-smi -i "$GPU" --query-gpu=index,memory.used,memory.free --format=csv,noheader
echo ""

echo "[vllm] Starting $MODEL_ID on port $PORT (GPU $GPU, single card) ..."

# Use the vllm env Python directly so $! captures the real process PID,
# not a conda run wrapper that exits immediately.
CMD=(
  env
    CUDA_VISIBLE_DEVICES="$GPU"
    HF_HOME="$HF_HOME_PATH"
    PYTHONUNBUFFERED=1
  "$VLLM_PYTHON" -m vllm.entrypoints.openai.api_server
    --model "$MODEL_ID"
    --port "$PORT"
    --host 127.0.0.1
    --trust-remote-code
    --tensor-parallel-size 1
    --gpu-memory-utilization 0.50
    --max-model-len 8192
    --enable-prefix-caching
    --disable-log-requests
)

if [[ "$BG" == "bg" ]]; then
    mkdir -p logs
    "${CMD[@]}" > logs/vllm_${PORT}.log 2>&1 &
    VLLM_PID=$!
    echo "$VLLM_PID" > vllm.pid
    echo "[vllm] Started. PID=$VLLM_PID"
    echo "[vllm] Logs:  tail -f logs/vllm_${PORT}.log"
    echo "[vllm] Wait for startup (2-5 min), then check:"
    echo "         curl -s http://localhost:${PORT}/health"
    echo "[vllm] Stop:  bash scripts/stop_vllm.sh"
else
    "${CMD[@]}"
fi
