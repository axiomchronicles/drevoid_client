"""
Drevoid - Advanced LAN Chat Application

A professional terminal-based chat application with room management,
private messaging, CTF flag detection, and real-time collaboration features.
"""

__version__ = "1.0.0"
__author__ = "Drevoid Contributors"
__license__ = "MIT"

from .core.protocol import MessageType, UserRole, RoomType
from .client.connection import ConnectionManager
from .server.server import ChatServer

__all__ = [
    "MessageType",
    "UserRole",
    "RoomType",
    "ConnectionManager",
    "ChatServer",
]
