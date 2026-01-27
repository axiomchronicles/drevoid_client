"""Flag detection and storage system."""

import re
import time
from dataclasses import dataclass
from typing import Dict, List
from .flag_patterns import get_all_patterns


@dataclass
class Flag:
    """Represents a captured flag."""

    content: str
    finder: str
    room: str
    timestamp: float
    message_preview: str

    def __eq__(self, other):
        """Compare flags by content."""
        if not isinstance(other, Flag):
            return False
        return self.content == other.content

    def __hash__(self):
        """Hash flag by content."""
        return hash(self.content)


class FlagDetector:
    """
    Detects and stores CTF flags in message content.

    Scans messages against predefined patterns and maintains
    a record of discovered flags with metadata.
    """

    def __init__(self):
        """Initialize flag detector with all patterns."""
        self.flags_found: Dict[str, Flag] = {}
        self.patterns = get_all_patterns()

    def detect(self, content: str) -> List[str]:
        """
        Detect flags in content using all patterns.

        Args:
            content: Text to scan for flags

        Returns:
            List of unique flag strings found
        """
        matches = []
        for pattern in self.patterns:
            found = re.findall(pattern, content, re.IGNORECASE)
            matches.extend(found)
        return list(set(matches))

    def store_flag(self, flag_content: str, finder: str, room: str, message_preview: str) -> bool:
        """
        Store a discovered flag.

        Args:
            flag_content: The flag string
            finder: Username who found it
            room: Room where flag was found
            message_preview: Preview of the message containing flag

        Returns:
            True if flag was new and stored, False if already recorded
        """
        if flag_content not in self.flags_found:
            self.flags_found[flag_content] = Flag(
                content=flag_content,
                finder=finder,
                room=room,
                timestamp=time.time(),
                message_preview=message_preview,
            )
            return True
        return False

    def get_all_flags(self) -> List[Flag]:
        """
        Retrieve all captured flags.

        Returns:
            List of Flag objects
        """
        return list(self.flags_found.values())

    def get_flag(self, flag_content: str) -> Flag | None:
        """
        Retrieve a specific flag by content.

        Args:
            flag_content: Flag string to search for

        Returns:
            Flag object or None if not found
        """
        return self.flags_found.get(flag_content)

    def get_flags_by_finder(self, finder: str) -> List[Flag]:
        """
        Get all flags found by a specific user.

        Args:
            finder: Username to filter by

        Returns:
            List of Flag objects found by user
        """
        return [f for f in self.flags_found.values() if f.finder == finder]

    def get_flags_by_room(self, room: str) -> List[Flag]:
        """
        Get all flags found in a specific room.

        Args:
            room: Room name to filter by

        Returns:
            List of Flag objects found in room
        """
        return [f for f in self.flags_found.values() if f.room == room]

    def clear(self) -> None:
        """Clear all stored flags."""
        self.flags_found.clear()

    def get_count(self) -> int:
        """Get total number of captured flags."""
        return len(self.flags_found)
