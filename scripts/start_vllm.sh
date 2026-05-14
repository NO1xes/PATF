#!/usr/bin/env bash
# Start vLLM with Qwen3-30B-A3B in OpenAI-compatible mode.
# Run this on the GPU server, NOT on local_pc_win11.
#
# Requirements:
#   - CUDA GPU with sufficient VRAM
#   - vLLM installed: pip install vllm
#   - Model downloaded or HF_ENDPOINT set
#
# Usage: bash scripts/start_vllm.sh [port]
set -euo pipefail

PORT="${1:-8000}"
MODEL="Qwen/Qwen3-30B-A3B"

echo "[vllm] Starting $MODEL on port $PORT ..."
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --port "$PORT" \
  --trust-remote-code \
  --enable-prefix-caching \
  --max-model-len 8192
