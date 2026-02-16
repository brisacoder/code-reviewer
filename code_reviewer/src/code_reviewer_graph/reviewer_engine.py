"""Implement multi-model reviewer orchestration for LangGraph reviewer node.

Args:
    None.

Returns:
    None.

Example:
    >>> state = {"target_files": ["src/example.py"]}
    >>> result = run_multi_model_review(state)
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel
from pydantic import Field

from code_reviewer_graph.settings import Settings
from code_reviewer_graph.settings import get_settings
from code_reviewer_graph.state import GraphState
from code_reviewer_graph.state import ModelReviewResult
from code_reviewer_graph.state import ReviewIssue
from code_reviewer_graph.state import ReviewReport
from code_reviewer_graph.state import ReviewViolation


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelRoute:
    """Represent one model endpoint route for OpenAI SDK requests.

    Args:
        name: Human-readable provider label.
        model: Model ID used with the Responses API.
        api_key: API key for the selected endpoint.
        base_url: Optional OpenAI-compatible base URL.

    Returns:
        None.

    Example:
        >>> route = ModelRoute(
        ...     name="openai",
        ...     model="gpt-5.2",
        ...     api_key="key",
        ...     base_url=None,
        ... )
    """

    name: str
    model: str
    api_key: str | None
    base_url: str | None


@dataclass(frozen=True)
class FilePayload:
    """Represent one target file content sent to reviewer models.

    Args:
        file_path: Relative or absolute path to reviewed file.
        content: Current text content for review.

    Returns:
        None.

    Example:
        >>> payload = FilePayload(file_path="app.py", content="print('x')")
    """

    file_path: str
    content: str


class StructuredIssue(BaseModel):
    """Describe one structured issue emitted by a reviewer model.

    Args:
        file_path: Reviewed file path.
        issue: Human-readable issue statement.
        violation: Rule name or identifier violated.
        suggested_fix: Concrete remediation instruction.

    Returns:
        None.

    Example:
        >>> issue = StructuredIssue(
        ...     file_path="src/a.py",
        ...     issue="Missing return type",
        ...     violation="Rule 20",
        ...     suggested_fix="Add return annotation",
        ... )
    """

    file_path: str = Field(min_length=1)
    issue: str = Field(min_length=1)
    violation: str = Field(min_length=1)
    suggested_fix: str = Field(min_length=1)


class StructuredIssuesResponse(BaseModel):
    """Represent normalized structured review payload from a model.

    Args:
        issues: List of structured issue records.

    Returns:
        None.

    Example:
        >>> result = StructuredIssuesResponse(issues=[])
    """

    issues: list[StructuredIssue]


def get_target_files(state: GraphState) -> list[str]:
    """Resolve target file pointers from graph state.

    Args:
        state: Current graph state with file references.

    Returns:
        Ordered list of file paths to review.

    Example:
        >>> files = get_target_files({"target_file": "src/app.py"})
        >>> files
        ['src/app.py']
    """

    target_files = state.get("target_files", [])
    if target_files:
        return target_files
    target_file = state.get("target_file", "")
    if target_file:
        return [target_file]
    return []


def read_file_payloads(file_paths: list[str]) -> list[FilePayload]:
    """Load file contents for all review targets.

    Args:
        file_paths: File paths to include in review prompts.

    Returns:
        File payload objects preserving file path and text content.

    Example:
        >>> payloads = read_file_payloads(["README.md"])
    """

    payloads: list[FilePayload] = []
    for file_path in file_paths:
        path_obj = Path(file_path)
        content = path_obj.read_text(encoding="utf-8")
        payloads.append(FilePayload(file_path=file_path, content=content))
    return payloads


def build_openai_route(settings: Settings) -> ModelRoute:
    """Construct route metadata for OpenAI review pass.

    Args:
        settings: Runtime settings used for endpoint configuration.

    Returns:
        Route metadata for the OpenAI review model.

    Example:
        >>> route = build_openai_route(get_settings())
    """

    return ModelRoute(
        name="openai",
        model=settings.openai_reviewer_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


def build_gemini_route(settings: Settings) -> ModelRoute:
    """Construct route metadata for Gemini review pass.

    Args:
        settings: Runtime settings used for endpoint configuration.

    Returns:
        Route metadata for the Gemini review model.

    Example:
        >>> route = build_gemini_route(get_settings())
    """

    return ModelRoute(
        name="gemini",
        model=settings.gemini_reviewer_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


def build_anthropic_route(settings: Settings) -> ModelRoute:
    """Construct route metadata for Anthropic consolidation pass.

    Args:
        settings: Runtime settings used for endpoint configuration.

    Returns:
        Route metadata for the Anthropic consolidation model.

    Example:
        >>> route = build_anthropic_route(get_settings())
    """

    return ModelRoute(
        name="anthropic",
        model=settings.anthropic_collator_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


def validate_route(route: ModelRoute) -> None:
    """Validate route credentials before making model requests.

    Args:
        route: Model route metadata.

    Returns:
        None.

    Example:
        >>> validate_route(ModelRoute("openai", "gpt-5.2", "key", None))
    """

    if route.api_key:
        return
    message = (
        "Operation failed: missing API key for reviewer route "
        f"'{route.name}' using model '{route.model}'. Suggested action: "
        f"set the required API key environment variable for '{route.name}' "
        "and retry."
    )
    raise RuntimeError(message)


def build_client(route: ModelRoute) -> OpenAI:
    """Build OpenAI SDK client for a route.

    Args:
        route: Model route metadata.

    Returns:
        Configured OpenAI client.

    Example:
        >>> route = ModelRoute("openai", "gpt-5.2", "key", None)
        >>> client = build_client(route)
    """

    validate_route(route)
    LOGGER.info(
        "Attempting to create model client in build_client for route=%s",
        route.name,
    )
    client = OpenAI(api_key=route.api_key, base_url=route.base_url)
    LOGGER.info(
        "Successfully created model client in build_client for route=%s",
        route.name,
    )
    return client


def read_rules_text(settings: Settings) -> str:
    """Read reviewer rules text from package-scoped rules file.

    Args:
        settings: Runtime settings containing rule file path override.

    Returns:
        Full rules text used in reviewer prompts.

    Example:
        >>> text = read_rules_text(get_settings())
    """

    rules_path = Path(settings.reviewer_rules_file)
    return rules_path.read_text(encoding="utf-8")


def build_per_file_review_prompt(
    file_payload: FilePayload,
    rules_text: str,
) -> str:
    """Build prompt for reviewing one file against coding standards.

    Args:
        file_payload: File path and content bundled for review.
        rules_text: Full coding standards text.

    Returns:
        Prompt text requesting a comprehensive file review.

    Example:
        >>> payload = FilePayload("a.py", "def x():\n    return 1\n")
        >>> prompt = build_per_file_review_prompt(payload, "rules")
    """

    return (
        "You are a strict code reviewer. Review exactly one file and detect "
        "all rule violations.\n\n"
        "Rules file content:\n"
        f"{rules_text}\n\n"
        "Target file path:\n"
        f"{file_payload.file_path}\n\n"
        "Target file content:\n"
        f"{file_payload.content}"
    )


def build_collation_prompt(
    openai_result: ModelReviewResult,
    gemini_result: ModelReviewResult,
    rules_text: str,
) -> str:
    """Build prompt for consolidating two model review outputs.

    Args:
        openai_result: Structured result from OpenAI review pass.
        gemini_result: Structured result from Gemini review pass.
        rules_text: Full coding standards text.

    Returns:
        Prompt text requesting one consolidated issues list.

    Example:
        >>> prompt = build_collation_prompt(
        ...     {"model": "a", "issues": []},
        ...     {"model": "b", "issues": []},
        ...     "rules",
        ... )
    """

    return (
        "You are a senior code review adjudicator. Consolidate and "
        "de-duplicate the issue lists from two reviewer models while "
        "preserving coverage.\n\n"
        "Rules file content:\n"
        f"{rules_text}\n\n"
        "OpenAI reviewer result:\n"
        f"{json.dumps(openai_result, ensure_ascii=False, indent=2)}\n\n"
        "Gemini reviewer result:\n"
        f"{json.dumps(gemini_result, ensure_ascii=False, indent=2)}"
    )


def run_structured_prompt(
    route: ModelRoute,
    prompt: str,
) -> StructuredIssuesResponse:
    """Run one Responses API call and parse structured output.

    Args:
        route: Route containing model and endpoint details.
        prompt: Prompt text with review instructions.

    Returns:
        Parsed structured issues payload.

    Example:
        >>> route = ModelRoute("openai", "gpt-5.2", "key", None)
        >>> _ = run_structured_prompt(route, "{}");
    """

    client = build_client(route)
    LOGGER.info(
        "Attempting Responses API call in run_structured_prompt for route=%s",
        route.name,
    )
    response = client.responses.parse(
        model=route.model,
        input=prompt,
        text_format=StructuredIssuesResponse,
    )
    LOGGER.info(
        "Successfully completed Responses API call in run_structured_prompt "
        "for route=%s",
        route.name,
    )
    payload = response.output_parsed
    if payload is None:
        message = (
            "Operation failed: model returned no structured payload in "
            "run_structured_prompt for route "
            f"'{route.name}' and model '{route.model}'. Suggested action: "
            "verify model structured-output support and retry."
        )
        raise RuntimeError(message)
    return payload


def convert_issues(issues: list[StructuredIssue]) -> list[ReviewIssue]:
    """Convert pydantic issues to graph-state typed dictionaries.

    Args:
        issues: Parsed structured issues from a model response.

    Returns:
        Typed issue dictionaries for graph state storage.

    Example:
        >>> converted = convert_issues([])
        >>> converted
        []
    """

    converted: list[ReviewIssue] = []
    for issue in issues:
        converted.append(
            {
                "file_path": issue.file_path,
                "issue": issue.issue,
                "violation": issue.violation,
                "suggested_fix": issue.suggested_fix,
            }
        )
    return converted


def review_files_with_model(
    route: ModelRoute,
    rules_text: str,
    file_payloads: list[FilePayload],
) -> ModelReviewResult:
    """Review all target files with one model and aggregate issues.

    Args:
        route: Route metadata for current model pass.
        rules_text: Full coding standards text.
        file_payloads: Packaged file path/content inputs.

    Returns:
        Aggregated model result including all file issues.

    Example:
        >>> route = ModelRoute("openai", "gpt-5.2", "key", None)
        >>> _ = review_files_with_model(route, "rules", [])
    """

    collected_issues: list[ReviewIssue] = []
    for file_payload in file_payloads:
        prompt = build_per_file_review_prompt(file_payload, rules_text)
        parsed = run_structured_prompt(route, prompt)
        issues = convert_issues(parsed.issues)
        collected_issues.extend(issues)
    return {"model": route.model, "issues": collected_issues}


def build_review_report(issues: list[ReviewIssue]) -> ReviewReport:
    """Convert consolidated issue list into legacy report shape.

    Args:
        issues: Consolidated issue list for all reviewed files.

    Returns:
        Review report with compatibility fields.

    Example:
        >>> report = build_review_report([])
        >>> report["is_compliant"]
        True
    """

    violations: list[ReviewViolation] = []
    issue_count = len(issues)
    for index, issue in enumerate(issues):
        violations.append(
            {
                "rule_id": f"CONS-{index + 1}",
                "standard": issue["violation"],
                "severity": "medium",
                "location": issue["file_path"],
                "message": issue["issue"],
                "suggestion": issue["suggested_fix"],
            }
        )

    summary = (
        f"Consolidated reviewer found {issue_count} issue(s) across "
        "provided files."
    )
    return {
        "summary": summary,
        "is_compliant": issue_count == 0,
        "violations": violations,
    }


def run_multi_model_review(state: GraphState) -> dict[str, object]:
    """Execute OpenAI->Gemini->Anthropic review pipeline.

    Args:
        state: Current graph state containing file pointers.

    Returns:
        Dictionary of state updates to merge in reviewer node.

    Example:
        >>> updates = run_multi_model_review({"target_files": ["README.md"]})
    """

    settings = get_settings()
    file_paths = get_target_files(state)
    file_payloads = read_file_payloads(file_paths)
    rules_text = read_rules_text(settings)

    openai_route = build_openai_route(settings)
    gemini_route = build_gemini_route(settings)
    anthropic_route = build_anthropic_route(settings)

    openai_review_result = review_files_with_model(
        openai_route,
        rules_text,
        file_payloads,
    )
    gemini_review_result = review_files_with_model(
        gemini_route,
        rules_text,
        file_payloads,
    )

    collation_prompt = build_collation_prompt(
        openai_review_result,
        gemini_review_result,
        rules_text,
    )
    consolidated = run_structured_prompt(anthropic_route, collation_prompt)
    consolidated_issues = convert_issues(consolidated.issues)
    consolidated_review_result: ModelReviewResult = {
        "model": anthropic_route.model,
        "issues": consolidated_issues,
    }
    review_report = build_review_report(consolidated_issues)

    return {
        "review_report": review_report,
        "review_issues": consolidated_issues,
        "review_satisfied": review_report["is_compliant"],
        "openai_review_result": openai_review_result,
        "gemini_review_result": gemini_review_result,
        "consolidated_review_result": consolidated_review_result,
    }
