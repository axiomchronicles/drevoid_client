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

    def mute(self, username: str, duration: str = "infinite") -> bool:
        """
        Mute user.

        Args:
            username: User to mute
            duration: Duration of mute (e.g., "1h", "30m", "infinite")

        Returns:
            True if successful
        """
        if not self.client.connected:
            from ..core.protocol import colorize, Colors

            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        from ..core.protocol import colorize, Colors

        print(f"{colorize(f'✅ Muted {username}', Colors.GREEN)}")
        return True

    def unmute(self, username: str) -> bool:
        """
        Unmute user.

        Args:
            username: User to unmute

        Returns:
            True if successful
        """
        if not self.client.connected:
            from ..core.protocol import colorize, Colors

            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        from ..core.protocol import colorize, Colors

        print(f"{colorize(f'✅ Unmuted {username}', Colors.GREEN)}")
        return True

    def promote(self, username: str, role: str = "moderator") -> bool:
        """
        Promote user to role.

        Args:
            username: User to promote
            role: Role to promote to (e.g., "moderator", "admin")

        Returns:
            True if successful
        """
        if not self.client.connected:
            from ..core.protocol import colorize, Colors

            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        from ..core.protocol import colorize, Colors

        print(f"{colorize(f'✅ Promoted {username} to {role}', Colors.GREEN)}")
        return True

    def demote(self, username: str) -> bool:
        """
        Demote user from role.

        Args:
            username: User to demote

        Returns:
            True if successful
        """
        if not self.client.connected:
            from ..core.protocol import colorize, Colors

            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        from ..core.protocol import colorize, Colors

        print(f"{colorize(f'✅ Demoted {username}', Colors.GREEN)}")
        return True
