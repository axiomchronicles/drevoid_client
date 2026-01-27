"""CTF flag detection and management module."""

from .flag_detector import FlagDetector
from .flag_patterns import FlagPattern

__all__ = ["FlagDetector", "FlagPattern"]
