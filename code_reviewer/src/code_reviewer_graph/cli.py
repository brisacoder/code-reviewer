"""Run a local demonstration of the LangGraph code-review workflow.

This CLI is intended as a smoke test for graph transitions and final state
shape before real writer/reviewer implementations are added.

Example:
    >>> main()
"""

from __future__ import annotations

import json
import logging

from code_reviewer_graph.graph import build_graph
from rich.console import Console


def main() -> None:
    """Execute a sample invocation and render final state to the terminal.

    Returns:
        None.

    Example:
        >>> main()
    """

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    console = Console()
    logger.info("Starting graph invocation in cli.main")
    graph = build_graph()
    final_state = graph.invoke(
        {
            "request": "Create or review target file",
            "desired_action": "review",
            "target_file": "example.py",
            "target_files": ["README.md"],
            "review_satisfied": True,
            "coding_standards": [
                "Follow PEP 8",
                "Add type hints",
                "Prefer pure functions when possible",
            ],
        }
    )
    logger.info("Completed graph invocation in cli.main")
    console.print_json(json.dumps(final_state))


if __name__ == "__main__":
    main()
