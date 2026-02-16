# Coding Standards — MANDATORY

**Every rule in this document is mandatory. There are no suggestions, no guidelines, no "when possible". Violation of any rule is a defect that must be fixed before the code is considered complete.**

**The Zen of Python governs all decisions not explicitly covered below.**

---

# Non-Negotiable Rules

These rules have ZERO exceptions. Do not work around them. Do not break them "just this once".

1. **NO import guards**: Never use `try ... from <package>` patterns
2. **NO imports inside functions or methods**: All imports go at the top of the file
3. **NO inner functions**: Define all functions at module or class level
4. **NO logic outside functions or classes**: Module-level declarations are allowed (constants, logger instantiation, `__all__`, type aliases). The only executable block allowed is `if __name__ == "__main__":`. Everything else goes inside a function or class
5. **NO circular imports**: Fix by refactoring to eliminate the circularity, never by lazy imports
6. **NO pickle**: Use Parquet for data serialization. Config files (JSON, YAML, TOML) are not affected by this rule
7. **NO bare except clauses**: Never `except:` or `except Exception: pass`
8. **NO print for diagnostic output**: Use the `logging` module for all diagnostic and operational output. For CLI user-facing output, use `rich` exclusively
9. **NO emojis** in code, commit messages, or documentation (unless explicitly requested)
10. **Activate the virtual environment** before any coding or testing
11. **Clean up all temporary files** created for testing, documentation, or experimentation

---

# Package Management

12. **Use `uv` exclusively** (not pip, poetry, or conda)
    - Install packages: `uv pip install <package>`
    - Run Python scripts: `uv run python <script>`
    - Run commands: `uv run <command>`
    - Update dependencies: `uv pip compile pyproject.toml`

# Project Structure

13. All local packages MUST be installed in editable mode: `uv add -e ./path/to/package`
14. snake_case for all Python files and directories
15. Test files: `test_<module_name>.py`

# Imports

16. Absolute imports only: `from package.module import name`
17. One `import`/`from` statement per line. Multiple names from the same module use parentheses:
    ```python
    from os.path import (
        exists,
        join,
    )
    ```
18. Ordering (blank line between groups): standard library, then third-party, then local packages
19. Alphabetical within each group

# Code Style

20. Type hints on **every** function parameter and return value (except `self` and `cls`)
21. PEP 8 compliance
22. Fix **all** linting errors before considering code complete
23. Maximum line length: 200 characters. Configure all tools (ruff, black, flake8) to match
24. Descriptive variable names over comments

# Docstrings

25. Required on: modules, classes, functions, and methods
26. Format: Google-style
27. Must include: description, Args (if any), Returns (if non-None), and at least one Example
28. Dunder methods do not require Examples
29. Must be meaningful and specific to the code — generic boilerplate is a defect
30. Update docstrings when changing function signatures

# Comments

31. Every comment must add information that the code itself cannot convey
32. Tag important comments and TODOs with `R. Penno`
33. AI-generated boilerplate comments are a defect — remove them

# Error Handling & Logging

## Exceptions

34. Catch **specific** exceptions only
35. Every caught exception must be logged AND re-raised. If an error is not worth re-raising, do not catch it — log the relevant condition instead
36. Errors must never pass silently

## Logging

37. Use structured logging with levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
38. Include context: function name, relevant IDs, operation being performed
39. Log before risky operations: "Attempting to connect to database..."
40. Log after critical operations: "Successfully processed 150 records"

## Error Messages

41. Must be actionable: "Failed to connect to database at localhost:5432. Check if service is running."
42. Include relevant context: user ID, file path, operation attempted
43. Format: "Operation failed: specific reason. Suggested action."
44. Tag critical errors with `R. Penno`

# Testing

45. Use `pytest` exclusively
    - Run all tests: `uv run pytest -v`
    - Run integration tests: `uv run pytest -v -m integration`
    - Run specific test: `uv run pytest -v path/to/test_file.py::test_function`
    - Integration tests are marked with `@pytest.mark.integration`

# Documentation

46. README must include: Purpose, Installation, Quick Start, Examples
47. Update README when adding features or changing installation steps
48. Keep README examples current and working
49. Update CHANGELOG.md for breaking changes and new features
50. Use semantic versioning
51. Document migration steps for breaking changes

---

# Compliance

**Before declaring work complete, verify every change against every rule above.** If anything does not comply, go back and fix it — do not declare "done." No AI agent (Claude, Codex, Copilot) is finished until full compliance is verified and confirmed. If a rule is ambiguous, the stricter interpretation applies.

## Report Delivery — Non-Negotiable

52. **The compliance checklist MUST appear inline in the chat response.** Every single time. No exceptions.
53. **NEVER save the compliance report to disk** as a markdown file, text file, or any other file format. The report is chat output, not a file artifact. If you have previously saved a report file, delete it.
54. **Every completed task gets its own compliance checklist.** This applies to the first task in a conversation AND every subsequent task. A conversation with five completed tasks must contain five compliance checklists. Skipping the report on later tasks is a defect.

## Report Format

**Required output before declaring "done":** Review every rule and produce a numbered compliance checklist. Use `done`, `N/A`, or `FAIL — [reason]` for each:

```
## Compliance Verification
1 - done
2 - N/A (no imports added)
3 - done
...
54 - done
```

Any `FAIL` means you are not done. **Do not report failures to the user. Do not ask whether to fix them. Do not pause, summarize, or wait for approval.** Fix every failure immediately, then re-run the full checklist. Repeat until every rule is `done` or `N/A` -- only then may you declare the work complete.

