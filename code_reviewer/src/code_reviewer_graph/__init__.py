"""Expose stable public entrypoints for the code reviewer graph package.

Consumers should import `build_graph` from this module rather than from
internal modules.

Example:
    >>> from code_reviewer_graph import build_graph
    >>> graph = build_graph()
"""

from typing import Any

from code_reviewer_graph.graph import build_graph as _build_graph


def build_graph() -> Any:
    """Return the compiled LangGraph app used by this package.

    Returns:
        A compiled LangGraph app.

    Example:
        >>> graph = build_graph()
    """

    return _build_graph()
