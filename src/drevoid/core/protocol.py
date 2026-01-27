"""
Core protocol definitions and utilities for Drevoid chat application.

This module defines the message types, serialization/deserialization logic,
and utilities for communication between client and server.
"""

import json
import struct
import threading
import hashlib
import time
from enum import Enum
from typing import Tuple, Optional


class MessageType(Enum):
    """Enumeration of all message types for client-server communication."""

    # Connection Management
    CONNECT = "connect"
    DISCONNECT = "disconnect"

    # Room Operations
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    LIST_ROOMS = "list_rooms"

    # Messaging
    MESSAGE = "message"
    PRIVATE_MESSAGE = "private_message"

    # User Management
    LIST_USERS = "list_users"
    KICK_USER = "kick_user"
    BAN_USER = "ban_user"

    # Admin
    ADMIN_COMMAND = "admin_command"

    # Status
    SUCCESS = "success"
    ERROR = "error"
    NOTIFICATION = "notification"

    # CTF/Flag Management
    FLAG_SUBMIT = "flag_submit"
    FLAG_LIST = "flag_list"
    FLAG_REQUEST = "flag_request"
    FLAG_RESPONSE = "flag_response"


class UserRole(Enum):
    """Enumeration of user roles in the system."""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class RoomType(Enum):
    """Enumeration of room types."""

    PUBLIC = "public"
    PRIVATE = "private"


def create_message(msg_type: MessageType, data: dict) -> dict:
    """
    Create a standardized message dictionary.

    Args:
        msg_type: The type of message (MessageType enum)
        data: Dictionary containing message payload

    Returns:
        Dictionary with type, timestamp, and data fields
    """
    return {
        "type": msg_type.value,
        "timestamp": time.time(),
        "data": data,
    }


def serialize_message(message: dict) -> bytes:
    """
    Serialize a message dictionary to bytes for transmission.

    Format: [4-byte length][JSON data]
    Uses big-endian unsigned int for length (network byte order)

    Args:
        message: Dictionary to serialize

    Returns:
        Bytes ready for socket transmission
    """
    json_data = json.dumps(message).encode("utf-8")
    length = len(json_data)
    return struct.pack("!I", length) + json_data


def deserialize_message(data: bytes) -> Tuple[Optional[dict], bytes]:
    """
    Deserialize bytes into a message dictionary.

    Handles partial messages by returning remaining buffer.

    Args:
        data: Raw bytes from socket

    Returns:
        Tuple of (parsed_message, remaining_buffer)
        If insufficient data: (None, original_data)
    """
    if len(data) < 4:
        return None, data

    length = struct.unpack("!I", data[:4])[0]
    if len(data) < 4 + length:
        return None, data

    json_data = data[4 : 4 + length]
    message = json.loads(json_data.decode("utf-8"))
    remaining = data[4 + length :]
    return message, remaining


def hash_password(password: str) -> str:
    """
    Hash a password using SHA256 for secure storage.

    Args:
        password: Plain text password

    Returns:
        Hexadecimal SHA256 hash
    """
    return hashlib.sha256(password.encode()).hexdigest()


def format_timestamp(timestamp: float) -> str:
    """
    Format a Unix timestamp to readable time string.

    Args:
        timestamp: Unix timestamp

    Returns:
        Formatted time string (HH:MM:SS)
    """
    return time.strftime("%H:%M:%S", time.localtime(timestamp))


class ThreadSafeDict:
    """
    Thread-safe dictionary wrapper using RLock for concurrent access.

    Provides thread-safe access to shared dictionary data without
    raising race conditions during concurrent operations.
    """

    def __init__(self):
        """Initialize thread-safe dictionary."""
        self._dict = {}
        self._lock = threading.RLock()

    def __getitem__(self, key):
        """Get item with lock protection."""
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key, value):
        """Set item with lock protection."""
        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key):
        """Delete item with lock protection."""
        with self._lock:
            del self._dict[key]

    def __contains__(self, key):
        """Check membership with lock protection."""
        with self._lock:
            return key in self._dict

    def get(self, key, default=None):
        """Get item with default, lock protected."""
        with self._lock:
            return self._dict.get(key, default)

    def keys(self):
        """Return list of keys (snapshot)."""
        with self._lock:
            return list(self._dict.keys())

    def values(self):
        """Return list of values (snapshot)."""
        with self._lock:
            return list(self._dict.values())

    def items(self):
        """Return list of items (snapshot)."""
        with self._lock:
            return list(self._dict.items())

    def pop(self, key, default=None):
        """Pop item with default, lock protected."""
        with self._lock:
            return self._dict.pop(key, default)

    def clear(self):
        """Clear all items with lock protection."""
        with self._lock:
            self._dict.clear()

    def update(self, other):
        """Update with another dict, lock protected."""
        with self._lock:
            self._dict.update(other)


class Colors:
    """ANSI color codes for terminal output styling."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    HIGHLIGHT = "\033[7m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


def colorize(text: str, color: str) -> str:
    """
    Add ANSI color codes to text for terminal output.

    Args:
        text: Text to colorize
        color: Color code from Colors class

    Returns:
        Colorized text string
    """
    return f"{color}{text}{Colors.RESET}"
