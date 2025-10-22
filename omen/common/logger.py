#!/usr/bin/env python3
"""
OMEN Logger - Colorful, toggleable logging utility.

Provides colorized console output using rich library with ability to
disable colors for non-interactive environments.
"""

import os
import sys
import logging
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Global state for color management
_COLORS_ENABLED = os.getenv("OMEN_NO_COLOR", "0") != "1"
_CONSOLE: Optional[Console] = None


# Custom theme for OMEN
OMEN_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "critical": "red bold reverse",
    "success": "green bold",
    "highlight": "magenta",
})


def enable_colors() -> None:
    """Enable colorized output."""
    global _COLORS_ENABLED
    _COLORS_ENABLED = True


def disable_colors() -> None:
    """Disable colorized output."""
    global _COLORS_ENABLED
    _COLORS_ENABLED = False


def get_console() -> Console:
    """Get or create the global Console instance."""
    global _CONSOLE
    if _CONSOLE is None:
        _CONSOLE = Console(
            theme=OMEN_THEME,
            force_terminal=_COLORS_ENABLED,
            no_color=not _COLORS_ENABLED,
            stderr=True,
        )
    return _CONSOLE


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        log_file: Optional file path for file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False

    # Console handler with Rich
    if _COLORS_ENABLED:
        console_handler = RichHandler(
            console=get_console(),
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
    
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def print_success(message: str) -> None:
    """Print a success message."""
    console = get_console()
    console.print(f"[success]✓[/success] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console = get_console()
    console.print(f"[error]✗[/error] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console = get_console()
    console.print(f"[warning]⚠[/warning] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console = get_console()
    console.print(f"[info]ℹ[/info] {message}")


def print_highlight(message: str) -> None:
    """Print a highlighted message."""
    console = get_console()
    console.print(f"[highlight]{message}[/highlight]")

