# Harvest Loop

Autonomous Farm Inspection Planning Platform — a solo learning build.
See the [Harvest Loop plan](../harvest-loop-plan.html) for the full
phase-by-phase roadmap. This repo currently contains **Phase 00:
Foundations & scaffolding** only.

## What's here right now

```
.devcontainer/       Codespace setup (installs uv + Ollama on first create)
src/harvest_loop/
  graph.py           The Phase 00 "hello graph": 2 LangGraph nodes, typed state
  llm.py             One place that builds the Ollama client
  agents/            Empty — Phase 02
  data/              Empty — Phase 01
  eval/              Empty — Phase 04
  serving/           Empty — Phase 05
  security/          Empty — Phase 06
tests/test_graph.py  Tests the graph's wiring against a FAKE llm (no model needed)
scripts/run_hello_graph.py   Manual run against a REAL local model
infra/, notebooks/   Empty — later phases
```

## First-time setup (inside the Codespace)

The devcontainer already installed `uv` and `Ollama` for you. You still
need to pull a model and start the Ollama server yourself — that's a
deliberate manual step, not something hidden in container startup.

```bash
ollama serve &                 # start the local model server (leave running)
ollama pull qwen2.5:1.5b       # ~1GB download, main model
ollama pull llama3.2:1b        # ~1.3GB download, smaller/faster alternative
```

## Running things

```bash
uv run pytest                              # fast, offline, no model needed
uv run python scripts/run_hello_graph.py   # talks to the real local model
```

Try changing the input:

```bash
uv run python scripts/run_hello_graph.py --farm "Talbrook Farm" --weather "heatwave, 38C"
```

Or point at the smaller model to feel the CPU speed difference:

```bash
uv run python scripts/run_hello_graph.py --model llama3.2:1b
```

## Everyday commands

```bash
uv sync              # install/update dependencies from pyproject.toml
uv run pytest -v     # run tests, verbose
uv run ruff check .  # lint
uv run ruff format .        # auto-format
uv run pre-commit run --all-files   # run all pre-commit hooks by hand
```
