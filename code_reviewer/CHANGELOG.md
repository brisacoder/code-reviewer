# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - 2026-02-15

### Added
- Initial `code_reviewer_graph` package scaffold under `src/`.
- LangGraph workflow with `entry`, `supervisor`, `writer`, and `reviewer` nodes.
- `Command`-based transitions for all node handoffs.
- OpenAI Responses API helper module using `openai>=2.21.0`.
- Environment settings loader using `python-dotenv`.
- CLI entrypoint `code-reviewer-graph`.
- README sections for Purpose, Installation, Quick Start, and Examples.
- Tooling config for line-length consistency (`ruff`, `black`, `flake8`).
