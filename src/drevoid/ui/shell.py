"""Interactive chat shell and command interface."""

import cmd
import os
from typing import TYPE_CHECKING

from ..core.protocol import Colors, colorize
from ..utils.emoji_aliases import EmojiAliases
from .moderation import ModerationCommands

if TYPE_CHECKING:
    from ..client.chat_client import ChatClient


class ChatShell(cmd.Cmd):
    """Interactive command shell for chat client."""

    def __init__(self, client: "ChatClient"):
        """
        Initialize chat shell.

        Args:
            client: Chat client instance
        """
        super().__init__()
        self.client = client
        self.moderation = ModerationCommands(client)
        self.setup_message_display()
        self.update_prompt()

    def setup_message_display(self) -> None:
        """Setup message display callback."""

        def display_callback(text: str):
            print(text)

        self.client.message_handler.subscribe(display_callback)

    def update_prompt(self) -> None:
        """Update shell prompt based on connection state."""
        if self.client.connected and self.client.username:
            room_info = f"#{self.client.current_room}" if self.client.current_room else "#no-room"
            self.prompt = (
                f"{colorize(self.client.username, Colors.CYAN)}"
                f"{colorize(room_info, Colors.BLUE)} > "
            )
        else:
            self.prompt = f"{colorize('Not connected', Colors.RED)} > "

    def show_prompt(self) -> None:
        """Display the prompt."""
        self.update_prompt()
        if hasattr(self, "stdout"):
            self.stdout.write(self.prompt)
            self.stdout.flush()

    def emptyline(self) -> None:
        """Handle empty line (do nothing)."""
        pass

    def default(self, line: str) -> None:
        """
        Handle non-command input as room message.

        Args:
            line: Input line
        """
        if not self.client.connected:
            print(f"{colorize('❌ Not connected. Use connect command first.', Colors.RED)}")
            return
        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room. Use join command first.', Colors.RED)}")
            return
        if line.strip():
            self.client.send_message(line.strip())

    def do_help(self, arg: str) -> None:
        """Display help information."""
        print(f"\n{colorize('🎯 Drevoid LAN Chat Commands:', Colors.BOLD)}")

        print(f"\n{colorize('Connection Commands:', Colors.YELLOW)}")
        print(f"  {colorize('connect [host] [port] [username]', Colors.CYAN)} - Connect to server")
        print(f"  {colorize('disconnect', Colors.CYAN)} - Disconnect from server")
        print(f"  {colorize('quit/exit', Colors.CYAN)} - Exit the application")

        print(f"\n{colorize('Room Commands:', Colors.YELLOW)}")
        print(f"  {colorize('join <room_name> [password]', Colors.CYAN)} - Join a room")
        print(f"  {colorize('leave', Colors.CYAN)} - Leave current room")
        print(f"  {colorize('create <room_name> [private] [password]', Colors.CYAN)} - Create a room")
        print(f"  {colorize('rooms', Colors.CYAN)} - List available rooms")
        print(f"  {colorize('users', Colors.CYAN)} - List users in current room")

        print(f"\n{colorize('Messaging Commands:', Colors.YELLOW)}")
        print(f"  {colorize('msg <username> <message>', Colors.CYAN)} - Send private message")
        print(f"  {colorize('pm <username> <message>', Colors.CYAN)} - Send private message (alias)")
        print(f"  {colorize('<message>', Colors.CYAN)} - Send message to current room")

        print(f"\n{colorize('CTF & Flag Commands:', Colors.YELLOW)}")
        print(f"  {colorize('flags', Colors.CYAN)} - Display all captured flags")
        print(f"  {colorize('flag-count', Colors.CYAN)} - Show total flags found")

        print(f"\n{colorize('Emoji Commands:', Colors.YELLOW)}")
        print(f"  {colorize('emojis', Colors.CYAN)} - Display all emoji aliases")

        print(f"\n{colorize('Moderation Commands:', Colors.YELLOW)}")
        print(f"  {colorize('kick <username>', Colors.CYAN)} - Kick user from room (mods only)")
        print(f"  {colorize('ban <username>', Colors.CYAN)} - Ban user from room (mods only)")

        print(f"\n{colorize('Other Commands:', Colors.YELLOW)}")
        print(f"  {colorize('status', Colors.CYAN)} - Show connection status")
        print(f"  {colorize('clear', Colors.CYAN)} - Clear screen")
        print(f"  {colorize('help', Colors.CYAN)} - Show this help\n")

    def do_connect(self, args: str) -> None:
        """Connect to server: connect [host] [port] [username]"""
        if self.client.connected:
            print(f"{colorize('❌ Already connected. Disconnect first.', Colors.RED)}")
            return

        parts = args.split()
        host = (
            parts[0]
            if parts
            else input(f"{colorize('Enter server host (localhost):', Colors.CYAN)} ").strip()
            or "localhost"
        )

        try:
            port = (
                int(parts[1])
                if len(parts) > 1
                else int(
                    input(f"{colorize('Enter server port (12345):', Colors.CYAN)} ").strip()
                    or "12345"
                )
            )
        except ValueError:
            print(f"{colorize('❌ Invalid port number', Colors.RED)}")
            return

        username = (
            parts[2]
            if len(parts) > 2
            else input(f"{colorize('Enter username:', Colors.CYAN)} ").strip()
        )

        if not username:
            print(f"{colorize('❌ Username is required', Colors.RED)}")
            return

        print(f"{colorize('🔄 Connecting to', Colors.YELLOW)} {host}:{port} {colorize('as', Colors.YELLOW)} {username}...")

        if self.client.connect(host, port, username):
            print(f"{colorize('✅ Connected successfully!', Colors.GREEN)}")
            self.update_prompt()
        else:
            print(f"{colorize('❌ Connection failed', Colors.RED)}")

    def do_disconnect(self, args: str) -> None:
        """Disconnect from server."""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        self.client.disconnect()
        self.update_prompt()

    def do_join(self, args: str) -> None:
        """Join room: join <room_name> [password]"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        parts = args.split(None, 1)
        if not parts:
            print(f"{colorize('❌ Usage: join <room_name> [password]', Colors.RED)}")
            return

        room_name = parts[0]
        password = parts[1] if len(parts) > 1 else ""

        if self.client.room_manager.join(room_name, password):
            self.update_prompt()

    def do_leave(self, args: str) -> None:
        """Leave current room."""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room', Colors.RED)}")
            return
        if self.client.room_manager.leave():
            self.update_prompt()

    def do_create(self, args: str) -> None:
        """Create room: create <room_name> [private] [password]"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        parts = args.split()
        if not parts:
            print(f"{colorize('❌ Usage: create <room_name> [private] [password]', Colors.RED)}")
            return

        room_name = parts[0]
        room_type = "private" if len(parts) > 1 and parts[1].lower() == "private" else "public"
        password = parts[2] if len(parts) > 2 else ""

        self.client.room_manager.create(room_name, room_type, password)

    def do_rooms(self, args: str) -> None:
        """List available rooms."""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        self.client.room_manager.list_rooms()

    def do_users(self, args: str) -> None:
        """List users in current room."""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room', Colors.RED)}")
            return
        self.client.room_manager.list_users()

    def do_msg(self, args: str) -> None:
        """Send private message: msg <username> <message>"""
        self._send_private_message(args)

    def do_pm(self, args: str) -> None:
        """Send private message (alias): pm <username> <message>"""
        self._send_private_message(args)

    def do_emojis(self, args: str) -> None:
        """Display available emoji aliases."""
        print(f"\n{colorize('😊 Emoji Aliases', Colors.BOLD + Colors.YELLOW)}")
        print(f"{colorize('Use these text patterns to add emojis to your messages:', Colors.GRAY)}\n")
        print(EmojiAliases.list_aliases())
        print(f"\n{colorize('Example:', Colors.YELLOW)} I love this :heart: :fire: :rocket:\n")

    def do_kick(self, args: str) -> None:
        """Kick user: kick <username>"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not args.strip():
            print(f"{colorize('❌ Usage: kick <username>', Colors.RED)}")
            return
        self.moderation.kick(args.strip())

    def do_ban(self, args: str) -> None:
        """Ban user: ban <username>"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not args.strip():
            print(f"{colorize('❌ Usage: ban <username>', Colors.RED)}")
            return
        self.moderation.ban(args.strip())

    def do_flags(self, args: str) -> None:
        """Display all captured flags."""
        self.client.display_flags()

    def do_flag_count(self, args: str) -> None:
        """Show total flags found."""
        count = len(self.client.flag_detector.get_all_flags())
        print(f"{colorize(f'🚩 Total flags captured: {count}', Colors.BOLD + Colors.YELLOW)}")

    def do_status(self, args: str) -> None:
        """Show connection status."""
        if self.client.connected:
            print(f"{colorize('✅ Connected as:', Colors.GREEN)} {self.client.username}")
            print(f"{colorize('🏠 Current room:', Colors.CYAN)} {self.client.current_room or 'None'}")
        else:
            print(f"{colorize('❌ Not connected', Colors.RED)}")

    def do_clear(self, args: str) -> None:
        """Clear screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def do_quit(self, args: str) -> bool:
        """Exit application: quit"""
        return self.do_exit(args)

    def do_exit(self, args: str) -> bool:
        """Exit application: exit"""
        if self.client.connected:
            self.client.disconnect()
        print(f"{colorize('👋 Goodbye!', Colors.GREEN)}")
        return True

    def _send_private_message(self, args: str) -> None:
        """Send private message helper."""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        parts = args.split(None, 1)
        if len(parts) < 2:
            print(f"{colorize('❌ Usage: msg <username> <message>', Colors.RED)}")
            return

        target_user = parts[0]
        content = parts[1]
        self.client.send_private_message(target_user, content)
