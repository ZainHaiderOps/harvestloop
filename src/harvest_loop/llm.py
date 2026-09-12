"""A single place that knows how to construct the LLM client.

Every later phase (Planning, Scheduling, Checking, ...) will import
`get_llm()` instead of constructing `ChatOllama` directly. That means:

- the model name and server URL live in one place (env vars, with
  sensible defaults for a fresh Codespace), and
- swapping Ollama for something else later (e.g. the vLLM/SGLang setup
  in Phase 05) means changing this one file, not every agent.
"""

from __future__ import annotations

import os

from langchain_ollama import ChatOllama

DEFAULT_MODEL = "qwen2.5:1.5b"
DEFAULT_BASE_URL = "http://localhost:11434"


def get_llm(
    model: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.2,
) -> ChatOllama:
    """Return a configured ChatOllama client.

    Reads HARVEST_LOOP_MODEL / OLLAMA_BASE_URL from the environment if the
    caller doesn't pass explicit values, falling back to small defaults
    that are realistic to run on a free Codespace's CPU.
    """
    resolved_model = model or os.environ.get("HARVEST_LOOP_MODEL", DEFAULT_MODEL)
    resolved_base_url = base_url or os.environ.get("OLLAMA_BASE_URL", DEFAULT_BASE_URL)
    return ChatOllama(model=resolved_model, base_url=resolved_base_url, temperature=temperature)
