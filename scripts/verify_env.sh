#!/usr/bin/env bash
# Verify the environment is set up correctly.
# Run after: conda activate agentprof && pip install -e ".[dev]"
set -euo pipefail

echo "=== Python ==="
python --version

echo "=== LangChain ==="
python -c "import langchain; print('langchain', langchain.__version__)"
python -c "import langchain_openai; print('langchain-openai', langchain_openai.__version__)"
python -c "import langgraph; print('langgraph', langgraph.__version__)"

echo "=== AgentProf package ==="
python -c "import agentprof; print('agentprof', agentprof.__version__)"

echo "=== .env ==="
if [ -f ".env" ]; then
  echo ".env found"
else
  echo "WARNING: .env not found — copy .env.example to .env"
fi

echo "=== All checks passed ==="
