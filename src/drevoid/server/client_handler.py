"""Client connection handler for server."""

import socket
import time
from typing import Tuple, Optional
from ..core.protocol import (
    serialize_message,
    deserialize_message,
    MessageType,
    create_message,
    ThreadSafeDict,
    hash_password,
)


class ClientHandler:
    """Handles individual client connections and requests."""

    def __init__(self, logger):
        """Initialize client handler."""
        self.logger = logger
        self.clients = ThreadSafeDict()  # username -> (socket, addr, role)
        self.flags_storage = ThreadSafeDict()

    def register_client(self, username: str, socket: socket.socket, addr: Tuple, role: str) -> bool:
        """
        Register a connected client.

        Args:
            username: Client username
            socket: Client socket
            addr: Client address tuple
            role: User role

        Returns:
            True if registered, False if username taken
        """
        if username in self.clients.keys():
            return False
        self.clients[username] = (socket, addr, role)
        return True

    def unregister_client(self, username: str) -> Optional[Tuple]:
        """Unregister client and return its info."""
        return self.clients.pop(username, None)

    def get_client_socket(self, username: str) -> Optional[socket.socket]:
        """Get client socket by username."""
        client_info = self.clients.get(username)
        return client_info[0] if client_info else None

    def get_client_role(self, username: str) -> Optional[str]:
        """Get client role by username."""
        client_info = self.clients.get(username)
        return client_info[2] if client_info else None

    def send_to_client(self, username: str, msg_type: MessageType, data: dict) -> bool:
        """
        Send message to specific client.

        Args:
            username: Target client username
            msg_type: Message type
            data: Message data

        Returns:
            True if sent successfully
        """
        sock = self.get_client_socket(username)
        if not sock:
            return False
        try:
            message = create_message(msg_type, data)
            sock.send(serialize_message(message))
            return True
        except Exception:
            return False

    def broadcast_to_room(
        self,
        room_manager,
        room_name: str,
        msg_type: MessageType,
        data: dict,
        exclude: Optional[str] = None,
    ) -> int:
        """
        Broadcast message to all users in room.

        Args:
            room_manager: Server room manager
            room_name: Target room
            msg_type: Message type
            data: Message data
            exclude: Username to exclude

        Returns:
            Number of users message was sent to
        """
        users = room_manager.get_room_users(room_name)
        sent_count = 0

        for user in users:
            if exclude and user == exclude:
                continue
            if room_manager.is_user_muted(user, room_name):
                continue
            if self.send_to_client(user, msg_type, data):
                sent_count += 1

        return sent_count

    def store_flag(self, flag_content: str, finder: str, room: str, preview: str) -> bool:
        """
        Store captured flag.

        Args:
            flag_content: Flag string
            finder: Username who found it
            room: Room where found
            preview: Message preview

        Returns:
            True if new flag, False if already stored
        """
        if flag_content in self.flags_storage.keys():
            return False

        self.flags_storage[flag_content] = {
            "content": flag_content,
            "finder": finder,
            "room": room,
            "timestamp": time.time(),
            "message_preview": preview,
        }
        return True

    def get_all_flags(self) -> list:
        """Get all stored flags."""
        return list(self.flags_storage.values())

    def get_flags_count(self) -> int:
        """Get total flags stored."""
        return len(self.flags_storage.keys())
