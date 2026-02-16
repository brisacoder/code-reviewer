"""Provide a minimal root CLI entrypoint for local verification.

Example:
    >>> main()
"""

import logging

from rich.console import Console


def main() -> None:
    """Run the root entrypoint and display a short status message.

    Returns:
        None.

    Example:
        >>> main()
    """

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting root entrypoint in main.main")
    console = Console()
    console.print("code-reviewer entrypoint is active.")


if __name__ == "__main__":
    main()
