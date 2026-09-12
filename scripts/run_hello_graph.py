"""Manual smoke test against a REAL local model.

Unlike tests/test_graph.py (which uses a fake LLM and needs nothing
running), this script talks to an actual Ollama server. Run it once
you've done, in the Codespace terminal:

    ollama serve &
    ollama pull qwen2.5:1.5b

Usage:
    uv run python scripts/run_hello_graph.py
    uv run python scripts/run_hello_graph.py --farm "Talbrook Farm" --weather "heatwave, 38C"
"""

from __future__ import annotations

import argparse

from harvest_loop.graph import build_graph
from harvest_loop.llm import get_llm


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--farm", default="Rossberg Orchard")
    parser.add_argument("--weather", default="40mm rain forecast over the next 3 days")
    parser.add_argument("--model", default=None, help="Overrides HARVEST_LOOP_MODEL")
    args = parser.parse_args()

    llm = get_llm(model=args.model)
    app = build_graph(llm)

    result = app.invoke(
        {
            "farm_name": args.farm,
            "weather_note": args.weather,
            "raw_model_output": None,
            "summary": None,
        }
    )

    print("Model said:\n ", result["raw_model_output"])
    print("\nSummary:\n ", result["summary"])


if __name__ == "__main__":
    main()
