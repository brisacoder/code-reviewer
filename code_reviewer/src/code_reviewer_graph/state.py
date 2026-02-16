"""Define typed state contracts for the code-review graph.

Args:
    None.

Returns:
    None.

Example:
    >>> sample_state: GraphState = {"request": "Review file.py"}
"""

from __future__ import annotations

from typing import Literal

from typing_extensions import TypedDict


class ReviewViolation(TypedDict):
    """Describe one standards violation found by the reviewer.

    Args:
        None.

    Returns:
        None.

    Example:
        >>> violation: ReviewViolation = {
        ...     "rule_id": "PEP8-001",
        ...     "standard": "PEP 8",
        ...     "severity": "medium",
        ...     "location": "example.py:10",
        ...     "message": "Line too long.",
        ...     "suggestion": "Wrap line to <= 100 chars.",
        ... }
    """

    rule_id: str
    standard: str
    severity: Literal["low", "medium", "high"]
    location: str
    message: str
    suggestion: str


class ReviewReport(TypedDict):
    """Represent structured reviewer output.

    Args:
        None.

    Returns:
        None.

    Example:
        >>> report: ReviewReport = {
        ...     "summary": "No violations.",
        ...     "is_compliant": True,
        ...     "violations": [],
        ... }
    """

    summary: str
    is_compliant: bool
    violations: list[ReviewViolation]


class ReviewIssue(TypedDict):
    """Represent one structured reviewer finding.

    Args:
        None.

    Returns:
        None.

    Example:
        >>> issue: ReviewIssue = {
        ...     "file_path": "src/module.py",
        ...     "issue": "Function has no docstring.",
        ...     "violation": "Rule 25: docstrings required",
        ...     "suggested_fix": "Add a Google-style docstring.",
        ... }
    """

    file_path: str
    issue: str
    violation: str
    suggested_fix: str


class ModelReviewResult(TypedDict):
    """Capture one model's structured review output.

    Args:
        None.

    Returns:
        None.

    Example:
        >>> result: ModelReviewResult = {
        ...     "model": "gpt-5.2",
        ...     "issues": [],
        ... }
    """

    model: str
    issues: list[ReviewIssue]


class GraphState(TypedDict, total=False):
    """Capture shared state passed through LangGraph nodes.

    Args:
        None.

    Returns:
        None.

    Example:
        >>> state: GraphState = {
        ...     "request": "Create utils.py",
        ...     "desired_action": "create",
        ...     "target_file": "utils.py",
        ... }
    """

    request: str
    desired_action: Literal["create", "modify", "review"]
    target_file: str
    target_files: list[str]
    coding_standards: list[str]

    draft_code: str
    writer_notes: str

    review_report: ReviewReport
    review_issues: list[ReviewIssue]
    openai_review_result: ModelReviewResult
    gemini_review_result: ModelReviewResult
    consolidated_review_result: ModelReviewResult
    review_satisfied: bool
    review_cycles: int
    max_review_cycles: int

    last_actor: Literal["entry", "supervisor", "writer", "reviewer"]
