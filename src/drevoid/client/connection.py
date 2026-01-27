"""Connection management for client-server communication."""

import socket
from typing import Optional
from ..core.protocol import (
    serialize_message,
    deserialize_message,
    MessageType,
    Colors,
    colorize,
    create_message,
)


class ConnectionManager:
    """Manages socket connection and data transmission with the server."""

    def __init__(self):
        """Initialize connection manager."""
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.username: Optional[str] = None

    def connect(self, host: str, port: int) -> bool:
        """
        Establish connection to server.

        Args:
            host: Server hostname or IP
            port: Server port

        Returns:
            True if successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            return True
        except Exception as e:
            print(f"{colorize('❌ Connection failed:', Colors.RED)} {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Close connection to server."""
        if self.connected and self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.connected = False

    def send_data(self, message: dict) -> bool:
        """
        Send message to server.

        Args:
            message: Message dictionary to send

        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            return False
        try:
            data = serialize_message(message)
            self.socket.send(data)
            return True
        except Exception as e:
            print(f"{colorize('❌ Send error:', Colors.RED)} {e}")
            self.connected = False
            return False

    def receive_data(self, buffer_size: int = 4096) -> Optional[bytes]:
        """
        Receive data from server.

        Args:
            buffer_size: Maximum bytes to receive

        Returns:
            Bytes received or None on error/disconnect
        """
        if not self.connected:
            return None
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                return None
            return data
        except Exception as e:
            if self.connected:
                # Only print error if it's not a "bad file descriptor" during shutdown
                if "Bad file descriptor" not in str(e):
                    print(f"{colorize('❌ Receive error:', Colors.RED)} {e}")
            return None
