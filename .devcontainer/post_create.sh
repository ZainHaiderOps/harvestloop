#!/usr/bin/env bash
# Runs once, automatically, the first time this Codespace is created.
# It only installs tools — it deliberately does NOT start Ollama or pull
# any model, because that's a slow, chunky download best done on purpose
# (and re-done manually if the Codespace is rebuilt), not hidden inside
# container startup.
set -euo pipefail

echo "==> Installing uv (Python package manager)"
curl -LsSf https://astral.sh/uv/install.sh | sh

echo "==> Installing Ollama (runs the local LLMs on CPU)"
curl -fsSL https://ollama.com/install.sh | sh

echo "==> Installing project dependencies with uv"
export PATH="$HOME/.local/bin:$PATH"
uv sync --group dev

echo "==> Installing the pre-commit git hook"
uv run pre-commit install

cat <<'EOF'

Setup finished. Next, in a terminal:

  1) ollama serve &
  2) ollama pull qwen2.5:1.5b
  3) ollama pull llama3.2:1b
  4) uv run pytest
  5) uv run python scripts/run_hello_graph.py

EOF
