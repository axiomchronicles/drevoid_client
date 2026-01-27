"""Moderation command utilities."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.chat_client import ChatClient


class ModerationCommands:
    """Handles moderation operations."""

    def __init__(self, client: "ChatClient"):
        """
        Initialize moderation commands.

        Args:
            client: Chat client instance
        """
        self.client = client

    def kick(self, username: str) -> bool:
        """
        Kick user from room.

        Args:
            username: User to kick

        Returns:
            True if successful
        """
        if not self.client.connected:
            from ..core.protocol import colorize, Colors

            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        return self.client.kick_user(username)

    def ban(self, username: str) -> bool:
        """
        Ban user from room.

        Args:
            username: User to ban

        Returns:
            True if successful
        """
        if not self.client.connected:
            from ..core.protocol import colorize, Colors

            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        return self.client.ban_user(username)
