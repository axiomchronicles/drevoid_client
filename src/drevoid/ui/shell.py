"""Interactive chat shell and command interface."""

import cmd
import os
from typing import TYPE_CHECKING

from ..core.protocol import Colors, colorize
from ..utils.emoji_aliases import EmojiAliases
from .moderation import ModerationCommands
from .ui_components import UIBox, StatusIndicator, FlagDisplay, UserDisplay, RoomDisplay, MenuBar

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
        print(UIBox.header("🎯 Drevoid LAN Chat Commands", 80))

        print(UIBox.section("Connection Commands", Colors.YELLOW))
        print(f"  {colorize('connect', Colors.CYAN):20} → Connect to server")
        print(f"  {colorize('disconnect', Colors.CYAN):20} → Disconnect from server")
        print(f"  {colorize('status', Colors.CYAN):20} → Show connection status")

        print(UIBox.section("Room Commands", Colors.YELLOW))
        print(f"  {colorize('join <room>', Colors.CYAN):20} → Join a room")
        print(f"  {colorize('leave', Colors.CYAN):20} → Leave current room")
        print(f"  {colorize('create <name>', Colors.CYAN):20} → Create a new room")
        print(f"  {colorize('rooms', Colors.CYAN):20} → List available rooms")
        print(f"  {colorize('users', Colors.CYAN):20} → List users in room")

        print(UIBox.section("Messaging Commands", Colors.YELLOW))
        print(f"  {colorize('msg <user> <text>', Colors.CYAN):20} → Send private message")
        print(f"  {colorize('<message>', Colors.CYAN):20} → Send message to room")

        print(UIBox.section("CTF & Flag Commands", Colors.YELLOW))
        print(f"  {colorize('flags', Colors.CYAN):20} → Display captured flags")
        print(f"  {colorize('flag-count', Colors.CYAN):20} → Show total flags")

        print(UIBox.section("Utilities", Colors.YELLOW))
        print(f"  {colorize('emojis', Colors.CYAN):20} → Show emoji aliases")
        print(f"  {colorize('clear', Colors.CYAN):20} → Clear screen")
        print(f"  {colorize('help', Colors.CYAN):20} → Show this help")

        print(UIBox.section("Moderation Commands", Colors.RED))
        print(f"  {colorize('kick <user>', Colors.CYAN):20} → Kick user from room (mods only)")
        print(f"  {colorize('ban <user>', Colors.CYAN):20} → Ban user from room (mods only)")

        print(UIBox.section("Exit Commands", Colors.YELLOW))
        print(f"  {colorize('quit/exit', Colors.CYAN):20} → Exit application")
        print()

    def do_connect(self, args: str) -> None:
        """Connect to server: connect [host] [port] [username]"""
        if self.client.connected:
            print(f"{StatusIndicator.ERROR} Already connected. Disconnect first.")
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
            print(f"{StatusIndicator.ERROR} Invalid port number")
            return

        username = (
            parts[2]
            if len(parts) > 2
            else input(f"{colorize('Enter username:', Colors.CYAN)} ").strip()
        )

        if not username:
            print(f"{StatusIndicator.ERROR} Username is required")
            return

        print(f"{StatusIndicator.LOADING} Connecting to {colorize(f'{host}:{port}', Colors.WHITE)} as {colorize(username, Colors.CYAN)}...")

        if self.client.connect(host, port, username):
            print(f"{StatusIndicator.SUCCESS} Connected successfully!")
            self.update_prompt()
        else:
            print(f"{StatusIndicator.ERROR} Connection failed")

    def do_disconnect(self, args: str) -> None:
        """Disconnect from server."""
        if not self.client.connected:
            print(f"{StatusIndicator.WARNING} Not connected")
            return
        self.client.disconnect()
        self.update_prompt()
        print(f"{StatusIndicator.SUCCESS} Disconnected")

    def do_join(self, args: str) -> None:
        """Join room: join <room_name> [password]"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        parts = args.split(None, 1)
        if not parts:
            print(f"{StatusIndicator.ERROR} Usage: {colorize('join <room_name>', Colors.CYAN)}")
            return

        room_name = parts[0]
        password = parts[1] if len(parts) > 1 else ""

        print(f"{StatusIndicator.LOADING} Joining {colorize(room_name, Colors.CYAN)}...")
        if self.client.room_manager.join(room_name, password):
            print(f"{StatusIndicator.SUCCESS} Joined {colorize(room_name, Colors.CYAN)}")
            self.update_prompt()

    def do_leave(self, args: str) -> None:
        """Leave current room."""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return
        if not self.client.current_room:
            print(f"{StatusIndicator.WARNING} Not in any room")
            return
        if self.client.room_manager.leave():
            print(f"{StatusIndicator.SUCCESS} Left room")
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
        flags = self.client.flag_detector.get_all_flags()
        print(FlagDisplay.format_flags_list(flags))

    def do_flag_count(self, args: str) -> None:
        """Show total flags found."""
        count = len(self.client.flag_detector.get_all_flags())
        emoji = StatusIndicator.FLAG
        print(f"\n{emoji} {colorize(f'Total flags captured: {count}', Colors.BOLD + Colors.YELLOW)}")

    def do_status(self, args: str) -> None:
        """Show connection status."""
        print(UIBox.header("Status", 80))
        if self.client.connected:
            print(UIBox.stat_row("Status:", "Connected", Colors.GREEN))
            print(UIBox.stat_row("Username:", self.client.username or "N/A", Colors.CYAN))
            print(UIBox.stat_row("Current Room:", self.client.current_room or "None", Colors.BLUE))
        else:
            print(UIBox.stat_row("Status:", "Not Connected", Colors.RED))
        print()

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
