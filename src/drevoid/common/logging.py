"""Logging utilities for Drevoid application."""

import time
from typing import Literal
from ..core.protocol import Colors, colorize


class Logger:
    """Application logger with color support."""

    def __init__(self, enable_timestamps: bool = True):
        """
        Initialize logger.

        Args:
            enable_timestamps: Whether to include timestamps in log output
        """
        self.enable_timestamps = enable_timestamps

    def _get_timestamp(self) -> str:
        """Get formatted timestamp."""
        if not self.enable_timestamps:
            return ""
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        return f"{colorize(ts, Colors.GRAY)} "

    def info(self, message: str) -> None:
        """Log info level message."""
        prefix = colorize("[INFO]", Colors.BLUE)
        print(f"{self._get_timestamp()}{prefix} {message}")

    def success(self, message: str) -> None:
        """Log success level message."""
        prefix = colorize("[SUCCESS]", Colors.GREEN)
        print(f"{self._get_timestamp()}{prefix} {message}")

    def warning(self, message: str) -> None:
        """Log warning level message."""
        prefix = colorize("[WARNING]", Colors.YELLOW)
        print(f"{self._get_timestamp()}{prefix} {message}")

    def error(self, message: str) -> None:
        """Log error level message."""
        prefix = colorize("[ERROR]", Colors.RED)
        print(f"{self._get_timestamp()}{prefix} {message}")

    def debug(self, message: str) -> None:
        """Log debug level message."""
        prefix = colorize("[DEBUG]", Colors.PURPLE)
        print(f"{self._get_timestamp()}{prefix} {message}")
