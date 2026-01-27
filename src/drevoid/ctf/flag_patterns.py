"""Flag pattern definitions for CTF detection."""

import re
from enum import Enum


class FlagPattern(Enum):
    """Regex patterns for detecting CTF flags in messages."""

    # Standard brace-based formats (most common)
    BRACE_FLAG = r"flag\{[^}]*\}"
    BRACE_FLAG_UPPER = r"FLAG\{[^}]*\}"
    BRACE_CTF = r"CTF\{[^}]*\}"
    BRACE_CTF_LOWER = r"ctf\{[^}]*\}"
    
    # Alternative delimiters for brace format
    BRACE_FLG = r"flg\{[^}]*\}"
    BRACE_FLG_UPPER = r"FLG\{[^}]*\}"
    
    # Square bracket format
    BRACKET_FLAG = r"flag\[[^\]]*\]"
    BRACKET_FLAG_UPPER = r"FLAG\[[^\]]*\]"
    BRACKET_CTF = r"CTF\[[^\]]*\]"
    
    # Colon separator format
    COLON_FLAG = r"flag:[A-Za-z0-9_\-=+/]*"
    COLON_FLAG_UPPER = r"FLAG:[A-Za-z0-9_\-=+/]*"
    COLON_CTF = r"CTF:[A-Za-z0-9_\-=+/]*"
    
    # Underscore prefix format (common in some platforms)
    PREFIX_FLAG = r"_FLAG_[A-Za-z0-9_\-]{3,}"
    PREFIX_FLAG_LOWER = r"_flag_[A-Za-z0-9_\-]{3,}"
    
    # Format: flag=<content> (some platforms use equals)
    EQUALS_FLAG = r"flag=[A-Za-z0-9_\-=+/]{3,}"
    EQUALS_FLAG_UPPER = r"FLAG=[A-Za-z0-9_\-=+/]{3,}"
    
    # Base64-like content (common for encoded flags)
    BASE64_FLAG = r"flag\{[A-Za-z0-9+/=]+\}"
    BASE64_CTF = r"CTF\{[A-Za-z0-9+/=]+\}"
    
    # Hexadecimal flags
    HEX_FLAG = r"flag\{[0-9a-fA-F]+\}"
    HEX_CTF = r"CTF\{[0-9a-fA-F]+\}"
    
    # Crypto hashes (MD5, SHA1, SHA256, SHA512)
    MD5_HASH = r"\b[a-f0-9]{32}\b"
    SHA1_HASH = r"\b[a-f0-9]{40}\b"
    SHA256_HASH = r"\b[a-f0-9]{64}\b"
    SHA512_HASH = r"\b[a-f0-9]{128}\b"
    
    # Common flag prefixes (HackTheBox, TryHackMe, etc.)
    HTB_FLAG = r"HTB\{[^}]*\}"
    THM_FLAG = r"THM\{[^}]*\}"
    PICOCTF_FLAG = r"picoCTF\{[^}]*\}"
    
    # Parentheses format
    PAREN_FLAG = r"flag\([^)]*\)"
    PAREN_FLAG_UPPER = r"FLAG\([^)]*\)"
    
    # Angle brackets format
    ANGLE_FLAG = r"flag<[^>]*>"
    ANGLE_FLAG_UPPER = r"FLAG<[^>]*>"
    
    # Special platforms
    INTIGRITI_FLAG = r"INTIGRITI\{[^}]*\}"
    BUGCROWD_FLAG = r"BUGCROWD\{[^}]*\}"


def get_all_patterns() -> list[str]:
    """Get all flag detection patterns.
    
    Returns:
        List of regex patterns ordered by priority (more specific first)
    """
    # Order matters: check more specific patterns first to avoid false positives
    priority_patterns = [
        # Specific platforms first (avoid overlap with generic patterns)
        FlagPattern.INTIGRITI_FLAG.value,
        FlagPattern.BUGCROWD_FLAG.value,
        FlagPattern.PICOCTF_FLAG.value,
        FlagPattern.HTB_FLAG.value,
        FlagPattern.THM_FLAG.value,
        
        # Standard formats (very reliable)
        FlagPattern.BRACE_FLAG.value,
        FlagPattern.BRACE_FLAG_UPPER.value,
        FlagPattern.BRACE_CTF.value,
        FlagPattern.BRACE_CTF_LOWER.value,
        FlagPattern.BRACE_FLG.value,
        FlagPattern.BRACE_FLG_UPPER.value,
        
        # Alternative delimiters
        FlagPattern.BRACKET_FLAG.value,
        FlagPattern.BRACKET_FLAG_UPPER.value,
        FlagPattern.BRACKET_CTF.value,
        FlagPattern.PAREN_FLAG.value,
        FlagPattern.PAREN_FLAG_UPPER.value,
        FlagPattern.ANGLE_FLAG.value,
        FlagPattern.ANGLE_FLAG_UPPER.value,
        
        # Separator formats
        FlagPattern.COLON_FLAG.value,
        FlagPattern.COLON_FLAG_UPPER.value,
        FlagPattern.COLON_CTF.value,
        FlagPattern.EQUALS_FLAG.value,
        FlagPattern.EQUALS_FLAG_UPPER.value,
        
        # Prefix formats
        FlagPattern.PREFIX_FLAG.value,
        FlagPattern.PREFIX_FLAG_LOWER.value,
        
        # Specialized content flags
        FlagPattern.BASE64_FLAG.value,
        FlagPattern.BASE64_CTF.value,
        FlagPattern.HEX_FLAG.value,
        FlagPattern.HEX_CTF.value,
        
        # Hashes (lowest priority - highest chance of false positives)
        FlagPattern.MD5_HASH.value,
        FlagPattern.SHA1_HASH.value,
        FlagPattern.SHA256_HASH.value,
        FlagPattern.SHA512_HASH.value,
    ]
    
    return priority_patterns
