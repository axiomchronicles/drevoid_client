"""
Common protocol definitions and utilities for the chat application
"""

import json
import struct
import threading
import hashlib
import time
from enum import Enum

class MessageType(Enum):
    """Message types for client-server communication"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    MESSAGE = "message"
    PRIVATE_MESSAGE = "private_message"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    CREATE_ROOM = "create_room"
    LIST_ROOMS = "list_rooms"
    LIST_USERS = "list_users"
    KICK_USER = "kick_user"
    BAN_USER = "ban_user"
    ADMIN_COMMAND = "admin_command"
    ERROR = "error"
    SUCCESS = "success"
    NOTIFICATION = "notification"
    FLAG_SUBMIT = "flag_submit"
    FLAG_LIST = "flag_list"

class UserRole(Enum):
    """User roles in the chat system"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

class RoomType(Enum):
    """Room types"""
    PUBLIC = "public"
    PRIVATE = "private"

def create_message(msg_type: MessageType, data: dict) -> dict:
    """Create a standardized message"""
    return {
        "type": msg_type.value,
        "timestamp": time.time(),
        "data": data
    }

def serialize_message(message: dict) -> bytes:
    """Serialize message to bytes for transmission"""
    json_data = json.dumps(message).encode('utf-8')
    length = len(json_data)
    return struct.pack('!I', length) + json_data

def deserialize_message(data: bytes) -> tuple:
    """Deserialize message from bytes"""
    if len(data) < 4:
        return None, data

    length = struct.unpack('!I', data[:4])[0]
    if len(data) < 4 + length:
        return None, data

    json_data = data[4:4+length]
    message = json.loads(json_data.decode('utf-8'))
    remaining = data[4+length:]
    return message, remaining

def hash_password(password: str) -> str:
    """Hash password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def format_timestamp(timestamp: float) -> str:
    """Format timestamp for display"""
    return time.strftime("%H:%M:%S", time.localtime(timestamp))

class ThreadSafeDict:
    """Thread-safe dictionary implementation"""
    def __init__(self):
        self._dict = {}
        self._lock = threading.RLock()

    def __getitem__(self, key):
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key, value):
        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key):
        with self._lock:
            del self._dict[key]

    def __contains__(self, key):
        with self._lock:
            return key in self._dict

    def get(self, key, default=None):
        with self._lock:
            return self._dict.get(key, default)

    def keys(self):
        with self._lock:
            return list(self._dict.keys())

    def values(self):
        with self._lock:
            return list(self._dict.values())

    def items(self):
        with self._lock:
            return list(self._dict.items())

    def pop(self, key, default=None):
        with self._lock:
            return self._dict.pop(key, default)

    def clear(self):
        with self._lock:
            self._dict.clear()

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

def colorize(text: str, color: str) -> str:
    """Add color to text"""
    return f"{color}{text}{Colors.RESET}"
