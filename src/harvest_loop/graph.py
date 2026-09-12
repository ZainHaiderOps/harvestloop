"""Phase 00 "hello graph": the smallest possible proof that state can flow
through two LangGraph nodes, one of which calls an LLM.

This is deliberately tiny and deliberately on-theme: `consult_model` is a
one-node sliver of what the real Planning agent will do in Phase 02
(look at a farm + a weather note and reason about it), and `summarize`
is a stand-in for the kind of post-processing every agent will need.

The LLM is passed in rather than constructed inside this module. That's
what lets `tests/test_graph.py` run the *entire graph* against a fake,
instant, offline stand-in object instead of a real model server — the
graph's wiring is tested completely separately from whether Ollama is
installed or reachable.
"""

from __future__ import annotations

from typing import Optional, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


class HelloState(TypedDict):
    """The one shared, typed state object every node reads from and writes to.

    Every future agent (Planning, Scheduling, Search, Checking, Optimizing)
    will extend this same pattern: one explicit schema, not each node
    inventing its own shape of dict.
    """

    farm_name: str
    weather_note: str
    raw_model_output: Optional[str]
    summary: Optional[str]


class InvokableLLM(Protocol):
    """The tiny bit of the LangChain chat-model interface this graph relies
    on. Both `ChatOllama` and the `FakeLLM` used in tests satisfy this.
    """

    def invoke(self, prompt: str): ...  # noqa: D102


def _as_text(response) -> str:
    """Chat models (like ChatOllama) return an AIMessage with a `.content`
    string; a plain test stub can just return a string directly. Support
    both so the node code doesn't care which one it's talking to.
    """
    return getattr(response, "content", response)


def make_consult_model_node(llm: InvokableLLM):
    """Build the `consult_model` node, closing over the injected LLM."""

    def consult_model(state: HelloState) -> dict:
        prompt = (
            f"Farm: {state['farm_name']}\n"
            f"Weather note: {state['weather_note']}\n"
            "In one sentence, say whether an inspector should visit this "
            "farm this week, and why."
        )
        response = llm.invoke(prompt)
        return {"raw_model_output": _as_text(response)}

    return consult_model


def summarize(state: HelloState) -> dict:
    """A non-LLM node: pure Python post-processing of the model's output.

    Not every node in an agent graph needs to call a model — this one
    exists to make that point early, and to give the graph a second,
    independently testable step.
    """
    raw = (state.get("raw_model_output") or "").strip()
    return {"summary": f"[{state['farm_name']}] {raw}"}


def build_graph(llm: InvokableLLM) -> CompiledStateGraph:
    """Wire the two nodes into a compiled, runnable graph.

    Shape: START -> consult_model -> summarize -> END.
    """
    graph = StateGraph(HelloState)
    graph.add_node("consult_model", make_consult_model_node(llm))
    graph.add_node("summarize", summarize)
    graph.add_edge(START, "consult_model")
    graph.add_edge("consult_model", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()
