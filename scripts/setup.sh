#!/usr/bin/env bash
# Run this by hand once per fresh Codespace: bash setup.sh
# (Nothing here runs automatically — no devcontainer, no hidden build step.)
set -euo pipefail

echo "==> Installing uv (Python package manager)"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

echo "==> Installing Ollama (runs the local LLMs on CPU)"
curl -fsSL https://ollama.com/install.sh | sh

echo "==> Installing project dependencies with uv"
uv sync --group dev

echo "==> Installing the pre-commit git hook"
uv run pre-commit install

cat <<'EOF'

Setup finished. Next:

  1) ollama serve &
  2) ollama pull qwen2.5:1.5b
  3) ollama pull llama3.2:1b
  4) uv run pytest
  5) uv run python scripts/run_hello_graph.py

EOF