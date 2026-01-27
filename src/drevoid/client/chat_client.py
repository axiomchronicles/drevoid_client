"""Main chat client orchestrator."""

import socket
import threading
import time
from typing import Optional

from .connection import ConnectionManager
from .room_manager import RoomManager
from .message_handler import MessageHandler
from ..core.protocol import MessageType, serialize_message, deserialize_message, create_message
from ..ctf.flag_detector import FlagDetector
from ..utils.emoji_aliases import EmojiAliases
from ..utils.notifications import NotificationManager


class MessageBuffer:
    """Handles buffering of partial messages from socket."""

    def __init__(self):
        """Initialize message buffer."""
        self.buffer = b""

    def add_data(self, data: bytes) -> None:
        """Add data to buffer."""
        self.buffer += data

    def get_message(self) -> tuple[Optional[dict], bool]:
        """
        Extract next complete message from buffer.

        Returns:
            Tuple of (message, has_message)
        """
        message, self.buffer = deserialize_message(self.buffer)
        return message, message is not None

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0


class ChatClient:
    """
    Main client application orchestrator.

    Coordinates connection, messaging, room management, and flag detection.
    """

    def __init__(self):
        """Initialize chat client."""
        self.connection_manager = ConnectionManager()
        self.room_manager = RoomManager(self.connection_manager)
        self.flag_detector = FlagDetector()
        self.notification_manager = NotificationManager()
        self.message_handler = MessageHandler(
            self.flag_detector,
            self.connection_manager,
            self.notification_manager,
        )
        self.message_buffer = MessageBuffer()
        self.shell = None
        self.receive_thread: Optional[threading.Thread] = None
        self._shutdown_requested = False

    @property
    def connected(self) -> bool:
        """Check if connected to server."""
        return self.connection_manager.connected

    @property
    def username(self) -> str | None:
        """Get current username."""
        return self.connection_manager.username

    @property
    def current_room(self) -> str | None:
        """Get current room name."""
        return self.room_manager.current_room

    def connect(self, host: str = "localhost", port: int = 12345, username: str = "") -> bool:
        """
        Connect to server.

        Args:
            host: Server hostname
            port: Server port
            username: Username to connect as

        Returns:
            True if successful
        """
        if not self.connection_manager.connect(host, port):
            return False

        self.connection_manager.username = username
        self.message_handler.set_username(username)

        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

        if username:
            connect_msg = create_message(MessageType.CONNECT, {"username": username})
            self.connection_manager.send_data(connect_msg)

        return True

    def disconnect(self) -> None:
        """Disconnect from server."""
        self._shutdown_requested = True
        if self.connected:
            try:
                disconnect_msg = create_message(MessageType.DISCONNECT, {})
                self.connection_manager.send_data(disconnect_msg)
            except Exception:
                pass
            self.connection_manager.disconnect()
        
        # Wait for receive thread to finish
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)

    def send_message(self, content: str) -> bool:
        """
        Send message to current room.

        Args:
            content: Message text

        Returns:
            True if successful
        """
        if not self.connected:
            return False
        message = create_message(MessageType.MESSAGE, {"content": content})
        return self.connection_manager.send_data(message)

    def send_private_message(self, target_user: str, content: str) -> bool:
        """
        Send private message to user.

        Args:
            target_user: Recipient username
            content: Message text

        Returns:
            True if successful
        """
        if not self.connected:
            return False
        message = create_message(
            MessageType.PRIVATE_MESSAGE,
            {"target": target_user, "content": content},
        )
        return self.connection_manager.send_data(message)

    def kick_user(self, username: str) -> bool:
        """Kick user from room (moderator action)."""
        if not self.connected:
            return False
        message = create_message(MessageType.KICK_USER, {"username": username})
        return self.connection_manager.send_data(message)

    def ban_user(self, username: str) -> bool:
        """Ban user from room (moderator action)."""
        if not self.connected:
            return False
        message = create_message(MessageType.BAN_USER, {"username": username})
        return self.connection_manager.send_data(message)

    def display_flags(self) -> None:
        """Display all captured flags locally."""
        from ..core.protocol import Colors, colorize, format_timestamp
        
        flags = self.flag_detector.get_all_flags()
        if not flags:
            print(f"{colorize('No flags found yet.', Colors.GRAY)}")
            return

        print(f"\n{colorize('🚩 Captured Flags:', Colors.BOLD + Colors.YELLOW)}")
        for idx, flag in enumerate(flags, 1):
            time_str = format_timestamp(flag.timestamp)
            finder = colorize(flag.finder, Colors.CYAN)
            room = colorize(f"#{flag.room}", Colors.BLUE)
            flag_content = colorize(flag.content, Colors.HIGHLIGHT + Colors.GREEN)
            print(f"  {idx}. [{time_str}] {finder} in {room}: {flag_content}")
            print(f"     Preview: {flag.message_preview}")

    def _receive_loop(self) -> None:
        """Receive and process messages from server (runs in thread)."""
        while self.connected and not self._shutdown_requested:
            data = self.connection_manager.receive_data()
            if data is None:
                break

            self.message_buffer.add_data(data)
            while True:
                message, has_message = self.message_buffer.get_message()
                if not has_message:
                    break
                if not self._shutdown_requested:
                    self.message_handler.handle(message, self.current_room or "")
                    if self.shell:
                        self.shell.show_prompt()

        self.connection_manager.disconnect()
        # Only print if not shutting down
        if not self._shutdown_requested and self.shell:
            from ..core.protocol import Colors, colorize

            try:
                print(
                    f"\n{colorize('Connection lost. Type connect to reconnect.', Colors.RED)}"
                )
            except Exception:
                pass
