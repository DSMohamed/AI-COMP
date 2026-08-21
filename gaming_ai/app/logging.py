"""Structured application logging with Rich console formatting."""

import logging
import sys
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the root logger for the application."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_time=True,
                show_level=True,
                show_path=False,
            )
        ],
    )
    logger = logging.getLogger("gaming_ai")
    logger.setLevel(level)
    return logger


def log_event(category: str, message: str, style: str = "bold cyan") -> None:
    """Print an eye-catching structured event badge."""
    console.print(f"[{style}][{category.upper()}][/{style}] {message}")
