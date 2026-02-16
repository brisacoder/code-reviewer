# Code Reviewer Graph (LangGraph)

## Purpose

Provide a LangGraph-based orchestration scaffold for a code-review workflow with:

- an entry node,
- a supervisor node,
- a writer node,
- a reviewer node,
- iterative `Command`-based routing until review is satisfied.

The current implementation intentionally keeps writer/reviewer business logic as placeholders so graph transitions can be validated first.

## Installation

From project root:

```bash
uv pip install -e .
```

## Quick Start

Run the graph CLI entrypoint:

```bash
uv run code-reviewer-graph
```

## Examples

Example graph flow:

1. `entry` receives a request to create or modify a file.
2. `supervisor` routes to `writer`.
3. `writer` returns draft output to `supervisor`.
4. `supervisor` routes to `reviewer`.
5. `reviewer` returns structured violations report.
6. `supervisor` loops to `writer` until compliant, then routes to end.

Example package modules:

- `src/code_reviewer_graph/graph.py` for node transitions.
- `src/code_reviewer_graph/state.py` for typed state/report schema.
- `src/code_reviewer_graph/openai_responses.py` for OpenAI Responses API helper.
- `src/code_reviewer_graph/settings.py` for `python-dotenv` settings resolution.
