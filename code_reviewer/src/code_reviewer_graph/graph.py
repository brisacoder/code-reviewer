"""Build the LangGraph orchestration workflow for code review.

Args:
    None.

Returns:
    None.

Example:
    >>> graph = build_graph()
    >>> isinstance(graph, object)
    True
"""

from __future__ import annotations

from typing import Any
from typing import cast

from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph
from langgraph.types import Command

from code_reviewer_graph.reviewer_engine import get_target_files
from code_reviewer_graph.reviewer_engine import run_multi_model_review
from code_reviewer_graph.state import GraphState


def entry_node(state: GraphState) -> Any:
    """Initialize orchestration defaults and route to the supervisor.

    Args:
        state: Current graph state received from START.

    Returns:
        A command routing to the supervisor node with normalized defaults.

    Example:
        >>> command = entry_node({"request": "Review app.py"})
        >>> command.goto
        'supervisor'
    """

    target_files = get_target_files(state)
    return Command(
        goto="supervisor",
        update={
            "last_actor": "entry",
            "target_files": target_files,
            "review_cycles": state.get("review_cycles", 0),
            "max_review_cycles": state.get("max_review_cycles", 2),
            "review_satisfied": state.get("review_satisfied", False),
        },
    )


def supervisor_node(
    state: GraphState,
) -> Any:
    """Choose the next node based on writer/reviewer progress.

    Args:
        state: Current graph state, including review flags and last actor.

    Returns:
        A command routing to writer, reviewer, or END.

    Example:
        >>> command = supervisor_node({"review_satisfied": True})
        >>> command.goto
        '__end__'
    """

    if state.get("review_satisfied", False):
        return Command(goto=END, update={"last_actor": "supervisor"})

    if state.get("last_actor") == "writer":
        return Command(goto="reviewer", update={"last_actor": "supervisor"})

    return Command(goto="writer", update={"last_actor": "supervisor"})


def writer_node(state: GraphState) -> Any:
    """Return placeholder writer output and route back to supervisor.

    Args:
        state: Current graph state with request and standards context.

    Returns:
        A command routing to supervisor with placeholder writer updates.

    Example:
        >>> command = writer_node({"draft_code": ""})
        >>> command.goto
        'supervisor'
    """

    writer_notes = (
        "Writer placeholder output; implement file creation/"
        "modification logic later."
    )
    return Command(
        goto="supervisor",
        update={
            "last_actor": "writer",
            "writer_notes": writer_notes,
            "draft_code": state.get("draft_code", ""),
        },
    )


def reviewer_node(state: GraphState) -> Any:
    """Run multi-model file review and return consolidated findings.

    Args:
        state: Current graph state, including file pointers and counters.

    Returns:
        A command routing to supervisor with consolidated review results.

    Example:
        >>> command = reviewer_node({"target_files": ["README.md"]})
        >>> command.goto
        'supervisor'
    """

    review_cycles = state.get("review_cycles", 0) + 1
    reviewer_updates = run_multi_model_review(state)

    return Command(
        goto="supervisor",
        update={
            "last_actor": "reviewer",
            "review_cycles": review_cycles,
            **reviewer_updates,
        },
    )


def build_graph() -> Any:
    """Construct and compile the LangGraph workflow.

    Args:
        None.

    Returns:
        A compiled LangGraph app ready for invocation.

    Example:
        >>> graph = build_graph()
        >>> final_state = graph.invoke({"request": "Review file.py"})
    """

    builder = StateGraph(cast(Any, GraphState))

    builder.add_node("entry", cast(Any, entry_node))
    builder.add_node("supervisor", cast(Any, supervisor_node))
    builder.add_node("writer", cast(Any, writer_node))
    builder.add_node("reviewer", cast(Any, reviewer_node))

    builder.add_edge(START, "entry")

    return builder.compile()
