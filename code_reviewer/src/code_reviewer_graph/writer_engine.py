"""Implement the writer agent engine for LangGraph writer node.

The writer engine sends each target file (with context, task prompt, review
feedback, and writer rules) to an LLM via the OpenAI Responses API using
structured output.  The LLM returns the complete file content which is then
persisted to disk.

Example:
    >>> state = {"target_files": ["src/example.py"], "request": "Add docstrings"}
    >>> result = run_writer(state)
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
from code_reviewer_graph.state import ReviewIssue
from code_reviewer_graph.state import WrittenFile


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WriterRoute:
    """Represent one model endpoint route for the writer LLM request.

    Args:
        name: Human-readable provider label.
        model: Model ID used with the Responses API.
        api_key: API key for the selected endpoint.
        base_url: Optional OpenAI-compatible base URL.

    Returns:
        None.

    Example:
        >>> route = WriterRoute(
        ...     name="anthropic",
        ...     model="anthropic/claude-opus-4.6",
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
    """Represent one target file sent to the writer model.

    Args:
        file_path: Relative or absolute path to the target file.
        content: Current text content of the file, or empty string for new files.

    Returns:
        None.

    Example:
        >>> payload = FilePayload(file_path="app.py", content="print('x')")
    """

    file_path: str
    content: str


@dataclass(frozen=True)
class ContextPayload:
    """Represent one context file provided to the writer model for reference.

    Args:
        file_path: Relative or absolute path to the context file.
        content: Full text content of the context file.

    Returns:
        None.

    Example:
        >>> ctx = ContextPayload(file_path="models.py", content="class User: ...")
    """

    file_path: str
    content: str


class StructuredFileOutput(BaseModel):
    """Describe the structured output returned by the writer model for one file.

    Args:
        file_path: Path where the file should be written.
        content: Complete file content produced by the model.
        action: Whether the file was created or modified.
        explanation: Brief explanation of changes made.

    Returns:
        None.

    Example:
        >>> output = StructuredFileOutput(
        ...     file_path="src/utils.py",
        ...     content="def add(a: int, b: int) -> int:\\n    return a + b\\n",
        ...     action="create",
        ...     explanation="Created utility module with add function.",
        ... )
    """

    file_path: str = Field(min_length=1)
    content: str = Field(min_length=1)
    action: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class StructuredWriterResponse(BaseModel):
    """Represent the normalized structured writer payload from the model.

    Args:
        file_output: The structured file output for one target file.

    Returns:
        None.

    Example:
        >>> response = StructuredWriterResponse(
        ...     file_output=StructuredFileOutput(
        ...         file_path="a.py",
        ...         content="pass",
        ...         action="create",
        ...         explanation="Stub file.",
        ...     ),
        ... )
    """

    file_output: StructuredFileOutput


def get_target_files(state: GraphState) -> list[str]:
    """Resolve target file pointers from graph state.

    Args:
        state: Current graph state with file references.

    Returns:
        Ordered list of file paths targeted for writing.

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


def read_file_payload(file_path: str) -> FilePayload:
    """Load file content for a single target file.

    If the file does not exist, returns an empty content string indicating
    that the writer should create it from scratch.

    Args:
        file_path: Path to the target file.

    Returns:
        File payload with path and current content (or empty for new files).

    Example:
        >>> payload = read_file_payload("README.md")
    """

    path_obj = Path(file_path)
    if path_obj.exists():
        content = path_obj.read_text(encoding="utf-8")
    else:
        content = ""
    return FilePayload(file_path=file_path, content=content)


def read_context_payloads(context_paths: list[str]) -> list[ContextPayload]:
    """Load file contents for all context files.

    Args:
        context_paths: File paths to include as reference context.

    Returns:
        Context payload objects preserving file path and text content.

    Example:
        >>> payloads = read_context_payloads(["models.py"])
    """

    payloads: list[ContextPayload] = []
    for file_path in context_paths:
        path_obj = Path(file_path)
        content = path_obj.read_text(encoding="utf-8")
        payloads.append(ContextPayload(file_path=file_path, content=content))
    return payloads


def build_writer_route(settings: Settings) -> WriterRoute:
    """Construct route metadata for the writer model.

    Args:
        settings: Runtime settings used for endpoint configuration.

    Returns:
        Route metadata for the writer model.

    Example:
        >>> route = build_writer_route(get_settings())
    """

    return WriterRoute(
        name="writer",
        model=settings.writer_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


def validate_route(route: WriterRoute) -> None:
    """Validate route credentials before making model requests.

    Args:
        route: Writer route metadata.

    Returns:
        None.

    Example:
        >>> validate_route(WriterRoute("writer", "model", "key", None))
    """

    if route.api_key:
        return
    message = (
        "Operation failed: missing API key for writer route "
        f"'{route.name}' using model '{route.model}'. Suggested action: "
        f"set the required API key environment variable for '{route.name}' "
        "and retry."
    )
    raise RuntimeError(message)


def build_client(route: WriterRoute) -> OpenAI:
    """Build OpenAI SDK client for a writer route.

    Args:
        route: Writer route metadata.

    Returns:
        Configured OpenAI client.

    Example:
        >>> route = WriterRoute("writer", "model", "key", None)
        >>> client = build_client(route)
    """

    validate_route(route)
    LOGGER.info(
        "Attempting to create model client in build_client for writer route=%s",
        route.name,
    )
    client = OpenAI(api_key=route.api_key, base_url=route.base_url)
    LOGGER.info(
        "Successfully created model client in build_client for writer route=%s",
        route.name,
    )
    return client


def read_writer_rules_text(settings: Settings) -> str:
    """Read writer rules text from package-scoped rules file.

    Args:
        settings: Runtime settings containing writer rule file path.

    Returns:
        Full writer rules text used in writer prompts.

    Example:
        >>> text = read_writer_rules_text(get_settings())
    """

    rules_path = Path(settings.writer_rules_file)
    return rules_path.read_text(encoding="utf-8")


def format_review_feedback(review_issues: list[ReviewIssue]) -> str:
    """Format review issues into a text block for the writer prompt.

    Args:
        review_issues: List of review issues from prior review cycles.

    Returns:
        Formatted text listing all review violations for the writer to address.

    Example:
        >>> text = format_review_feedback([])
        >>> text
        'No review feedback provided.'
    """

    if not review_issues:
        return "No review feedback provided."
    return json.dumps(review_issues, ensure_ascii=False, indent=2)


def build_per_file_writer_prompt(
    file_payload: FilePayload,
    context_payloads: list[ContextPayload],
    rules_text: str,
    task_prompt: str,
    review_feedback: str,
) -> str:
    """Build prompt for writing or modifying one file.

    Args:
        file_payload: Target file path and current content.
        context_payloads: Reference files for additional context.
        rules_text: Full writer rules text.
        task_prompt: The user task description or request.
        review_feedback: Formatted review feedback from prior cycles.

    Returns:
        Prompt text requesting the complete file output.

    Example:
        >>> payload = FilePayload("a.py", "")
        >>> prompt = build_per_file_writer_prompt(payload, [], "rules", "Create a.py", "None")
    """

    context_section = ""
    if context_payloads:
        context_parts: list[str] = []
        for ctx in context_payloads:
            context_parts.append(
                f"Context file: {ctx.file_path}\n"
                f"Content:\n{ctx.content}\n"
            )
        context_section = (
            "Reference context files:\n\n"
            + "\n---\n".join(context_parts)
            + "\n\n"
        )

    existing_content_section = ""
    if file_payload.content:
        existing_content_section = (
            "Existing file content (modify as needed):\n"
            f"{file_payload.content}\n\n"
        )
    else:
        existing_content_section = (
            "This is a new file. Create it from scratch.\n\n"
        )

    return (
        "You are a strict code writer agent. Write or modify exactly one file "
        "following every rule below. Return the COMPLETE file content.\n\n"
        "Writer rules:\n"
        f"{rules_text}\n\n"
        "Task:\n"
        f"{task_prompt}\n\n"
        f"Target file path: {file_payload.file_path}\n\n"
        f"{existing_content_section}"
        f"{context_section}"
        "Review feedback from prior cycles:\n"
        f"{review_feedback}"
    )


def run_structured_writer_prompt(
    route: WriterRoute,
    prompt: str,
) -> StructuredWriterResponse:
    """Run one Responses API call for the writer and parse structured output.

    Args:
        route: Route containing model and endpoint details.
        prompt: Prompt text with writer instructions.

    Returns:
        Parsed structured writer response payload.

    Example:
        >>> route = WriterRoute("writer", "model", "key", None)
        >>> _ = run_structured_writer_prompt(route, "{}");
    """

    client = build_client(route)
    LOGGER.info(
        "Attempting Responses API call in run_structured_writer_prompt for route=%s",
        route.name,
    )
    response = client.responses.parse(
        model=route.model,
        input=prompt,
        text_format=StructuredWriterResponse,
    )
    LOGGER.info(
        "Successfully completed Responses API call in run_structured_writer_prompt for route=%s",
        route.name,
    )
    payload = response.output_parsed
    if payload is None:
        message = (
            "Operation failed: model returned no structured payload in "
            "run_structured_writer_prompt for route "
            f"'{route.name}' and model '{route.model}'. Suggested action: "
            "verify model structured-output support and retry."
        )
        raise RuntimeError(message)
    return payload


def persist_written_file(file_path: str, content: str) -> None:
    """Write the model-generated file content to disk.

    Creates parent directories as needed before writing.

    Args:
        file_path: Destination path for the written file.
        content: Complete file content to write.

    Returns:
        None.

    Example:
        >>> persist_written_file("/tmp/test_output.py", "pass\\n")
    """

    path_obj = Path(file_path)
    LOGGER.info(
        "Attempting to write file in persist_written_file for path=%s",
        file_path,
    )
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(content, encoding="utf-8")
    LOGGER.info(
        "Successfully wrote file in persist_written_file for path=%s",
        file_path,
    )


def convert_to_written_file(
    output: StructuredFileOutput,
) -> WrittenFile:
    """Convert a structured model output into a graph-state WrittenFile.

    Args:
        output: Parsed structured file output from the writer model.

    Returns:
        Typed WrittenFile dictionary for graph state storage.

    Example:
        >>> from code_reviewer_graph.writer_engine import StructuredFileOutput
        >>> out = StructuredFileOutput(
        ...     file_path="a.py", content="pass", action="create", explanation="stub",
        ... )
        >>> wf = convert_to_written_file(out)
        >>> wf["file_path"]
        'a.py'
    """

    action = "modify" if output.action.lower() == "modify" else "create"
    return {
        "file_path": output.file_path,
        "content": output.content,
        "action": action,
    }


def write_file_with_model(
    route: WriterRoute,
    rules_text: str,
    task_prompt: str,
    review_feedback: str,
    file_payload: FilePayload,
    context_payloads: list[ContextPayload],
) -> WrittenFile:
    """Send one file to the writer model, persist the result, and return state.

    Args:
        route: Writer route metadata.
        rules_text: Full writer rules text.
        task_prompt: The user task description or request.
        review_feedback: Formatted review feedback from prior cycles.
        file_payload: Target file path and current content.
        context_payloads: Reference context files.

    Returns:
        WrittenFile dictionary capturing what was written.

    Example:
        >>> route = WriterRoute("writer", "model", "key", None)
        >>> _ = write_file_with_model(route, "rules", "task", "none", FilePayload("a.py", ""), [])
    """

    prompt = build_per_file_writer_prompt(
        file_payload,
        context_payloads,
        rules_text,
        task_prompt,
        review_feedback,
    )
    parsed = run_structured_writer_prompt(route, prompt)
    file_output = parsed.file_output
    persist_written_file(file_output.file_path, file_output.content)
    return convert_to_written_file(file_output)


def run_writer(state: GraphState) -> dict[str, object]:
    """Execute the writer pipeline for all target files.

    For each target file, the writer builds a prompt incorporating the task
    request, writer rules, context files, existing content, and any prior
    review feedback.  The model returns complete file content via structured
    output, which is persisted to disk.

    Args:
        state: Current graph state containing file pointers and task context.

    Returns:
        Dictionary of state updates to merge in the writer node.

    Example:
        >>> updates = run_writer({"target_files": ["README.md"], "request": "Update README"})
    """

    settings = get_settings()
    file_paths = get_target_files(state)
    context_paths = state.get("context_files", [])
    task_prompt = state.get("request", "")
    review_issues = state.get("review_issues", [])

    rules_text = read_writer_rules_text(settings)
    review_feedback = format_review_feedback(review_issues)
    context_payloads = read_context_payloads(context_paths)
    route = build_writer_route(settings)

    written_files: list[WrittenFile] = []
    writer_notes_parts: list[str] = []

    for file_path in file_paths:
        file_payload = read_file_payload(file_path)
        written_file = write_file_with_model(
            route,
            rules_text,
            task_prompt,
            review_feedback,
            file_payload,
            context_payloads,
        )
        written_files.append(written_file)
        writer_notes_parts.append(
            f"Wrote {written_file['file_path']} ({written_file['action']})"
        )

    writer_notes = "; ".join(writer_notes_parts) if writer_notes_parts else "No files written."

    return {
        "written_files": written_files,
        "writer_notes": writer_notes,
    }
