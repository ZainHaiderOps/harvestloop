"""Tests for the Phase 00 hello graph.

Notice what these tests do NOT do: they never start Ollama, never make a
network call, and never depend on which model is pulled. They inject a
`FakeLLM` instead, so they run in milliseconds, work identically in CI,
and test exactly one thing — that the graph's wiring and state handling
are correct. Whether the *real* model gives a sensible answer is a
separate, manual check (see scripts/run_hello_graph.py), because that's
inherently non-deterministic and not something a unit test should assert
on.
"""

from harvest_loop.graph import HelloState, build_graph


class FakeLLM:
    """A minimal stand-in for ChatOllama: same `.invoke()` shape, no model
    server required, and it remembers what it was asked so tests can
    assert on the prompt too.
    """

    def __init__(self, canned_response: str):
        self.canned_response = canned_response
        self.calls: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.canned_response


def make_initial_state(**overrides) -> HelloState:
    state: HelloState = {
        "farm_name": "Rossberg Orchard",
        "weather_note": "40mm rain forecast over the next 3 days",
        "raw_model_output": None,
        "summary": None,
    }
    state.update(overrides)
    return state


def test_graph_runs_end_to_end_and_produces_a_summary():
    fake_llm = FakeLLM(
        "Yes, visit this week: heavy rain raises the risk of drainage "
        "and root-rot issues that are easiest to catch early."
    )
    app = build_graph(fake_llm)

    result = app.invoke(make_initial_state())

    assert result["raw_model_output"] == fake_llm.canned_response
    assert result["summary"] == f"[Rossberg Orchard] {fake_llm.canned_response}"


def test_consult_model_node_sends_farm_context_to_the_llm():
    fake_llm = FakeLLM("irrelevant for this test")
    app = build_graph(fake_llm)

    app.invoke(make_initial_state(farm_name="Talbrook Farm", weather_note="heatwave, 38C"))

    assert len(fake_llm.calls) == 1
    prompt = fake_llm.calls[0]
    assert "Talbrook Farm" in prompt
    assert "heatwave, 38C" in prompt


def test_summarize_handles_empty_model_output_gracefully():
    fake_llm = FakeLLM("")
    app = build_graph(fake_llm)

    result = app.invoke(make_initial_state())

    # No exception, and the farm name still ends up in the summary even
    # when the "model" returned nothing — a real model call can and will
    # occasionally do this, so the graph should degrade, not crash.
    assert result["summary"] == "[Rossberg Orchard] "
