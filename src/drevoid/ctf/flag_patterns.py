"""Flag pattern definitions for CTF detection."""

import re
from enum import Enum


class FlagPattern(Enum):
    """Regex patterns for detecting CTF flags in messages."""

    BRACE_FLAG = r"flag\{[^}]+\}"
    BRACE_FLAG_UPPER = r"FLAG\{[^}]+\}"
    BRACE_CTF = r"CTF\{[^}]+\}"
    BRACE_CTF_LOWER = r"ctf\{[^}]+\}"
    COLON_FLAG = r"flag:[A-Za-z0-9_\-]+"
    COLON_FLAG_UPPER = r"FLAG:[A-Za-z0-9_\-]+"
    MD5_HASH = r"[a-f0-9]{32}(?![a-f0-9])"
    SHA1_HASH = r"[a-f0-9]{40}(?![a-f0-9])"
    SHA256_HASH = r"[a-f0-9]{64}(?![a-f0-9])"


def get_all_patterns() -> list[str]:
    """Get all flag detection patterns."""
    return [pattern.value for pattern in FlagPattern]
