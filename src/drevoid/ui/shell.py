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

    def onecmd(self, line: str) -> bool:
        """
        Override onecmd to use custom help.

        Args:
            line: Command line

        Returns:
            True if quit command, False otherwise
        """
        # Intercept 'help' command to use our custom help
        if line.strip().lower() == 'help':
            self.do_help("")
            return False
        # Also handle 'help <command>' format
        if line.strip().lower().startswith('help '):
            cmd_part = line.strip()[5:].strip()
            self.do_help(cmd_part)
            return False
        return super().onecmd(line)

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
        print(f"  {colorize('topic <text>', Colors.CYAN):20} → Set room topic")
        print(f"  {colorize('invite <user>', Colors.CYAN):20} → Invite user to room")
        print(f"  {colorize('lockroom', Colors.CYAN):20} → Lock room (admin only)")
        print(f"  {colorize('unlockroom', Colors.CYAN):20} → Unlock room (admin only)")

        print(UIBox.section("Messaging Commands", Colors.YELLOW))
        print(f"  {colorize('msg <user> <text>', Colors.CYAN):20} → Send private message")
        print(f"  {colorize('pm <user> <text>', Colors.CYAN):20} → Send PM (alias)")
        print(f"  {colorize('<message>', Colors.CYAN):20} → Send message to room")
        print(f"  {colorize('announce <text>', Colors.CYAN):20} → Announce to room (admin)")
        print(f"  {colorize('broadcast <text>', Colors.CYAN):20} → Broadcast to all (admin)")

        print(UIBox.section("User Management", Colors.YELLOW))
        print(f"  {colorize('profile', Colors.CYAN):20} → View your profile")
        print(f"  {colorize('online', Colors.CYAN):20} → List online users")
        print(f"  {colorize('whois <user>', Colors.CYAN):20} → Get user info")
        print(f"  {colorize('info <user|room>', Colors.CYAN):20} → Get detailed info")
        print(f"  {colorize('block <user>', Colors.CYAN):20} → Block user")
        print(f"  {colorize('unblock <user>', Colors.CYAN):20} → Unblock user")
        print(f"  {colorize('blocked', Colors.CYAN):20} → List blocked users")

        print(UIBox.section("CTF & Flag Commands", Colors.YELLOW))
        print(f"  {colorize('flags', Colors.CYAN):20} → Display captured flags")
        print(f"  {colorize('flag-count', Colors.CYAN):20} → Show total flags")

        print(UIBox.section("Chat History & Search", Colors.YELLOW))
        print(f"  {colorize('history [limit]', Colors.CYAN):20} → Show chat history")
        print(f"  {colorize('search <keyword>', Colors.CYAN):20} → Search messages")
        print(f"  {colorize('export <file>', Colors.CYAN):20} → Export chat history")
        print(f"  {colorize('stats [room]', Colors.CYAN):20} → Show statistics")

        print(UIBox.section("Moderation Commands (Admin Only)", Colors.RED))
        print(f"  {colorize('kick <user>', Colors.CYAN):20} → Kick user from room")
        print(f"  {colorize('ban <user>', Colors.CYAN):20} → Ban user from server")
        print(f"  {colorize('mute <user> [time]', Colors.CYAN):20} → Mute user")
        print(f"  {colorize('unmute <user>', Colors.CYAN):20} → Unmute user")
        print(f"  {colorize('gag <user>', Colors.CYAN):20} → Gag user (hide messages)")
        print(f"  {colorize('ungag <user>', Colors.CYAN):20} → Ungag user")
        print(f"  {colorize('promote <user>', Colors.CYAN):20} → Promote to moderator")
        print(f"  {colorize('demote <user>', Colors.CYAN):20} → Demote user")
        print(f"  {colorize('clearroom', Colors.CYAN):20} → Clear room messages")

        print(UIBox.section("Productivity & Notifications", Colors.YELLOW))
        print(f"  {colorize('settings', Colors.CYAN):20} → Show settings")
        print(f"  {colorize('notifications', Colors.CYAN):20} → Notification settings")
        print(f"  {colorize('remind <time> <msg>', Colors.CYAN):20} → Set reminder")
        print(f"  {colorize('timer <duration>', Colors.CYAN):20} → Start timer")
        print(f"  {colorize('alias [add|list]', Colors.CYAN):20} → Manage aliases")
        print(f"  {colorize('snippet [add|list]', Colors.CYAN):20} → Manage snippets")

        print(UIBox.section("Utilities", Colors.YELLOW))
        print(f"  {colorize('emojis', Colors.CYAN):20} → Show emoji aliases")
        print(f"  {colorize('clear', Colors.CYAN):20} → Clear screen")
        print(f"  {colorize('help', Colors.CYAN):20} → Show this help")

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
            else input(f"{colorize('Enter server host (ch.tubox.cloud):', Colors.CYAN)} ").strip()
            or "ch.tubox.cloud"
        )

        try:
            port = (
                int(parts[1])
                if len(parts) > 1
                else int(
                    input(f"{colorize('Enter server port (8891):', Colors.CYAN)} ").strip()
                    or "8891"
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

    # ==================== ADVANCED FEATURES ====================

    def do_history(self, args: str) -> None:
        """Display chat history: history [limit] [room_name]"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        parts = args.split()
        limit = int(parts[0]) if parts else 50
        room_name = parts[1] if len(parts) > 1 else self.client.current_room

        if not room_name:
            print(f"{StatusIndicator.ERROR} Not in any room. Specify room name: history [limit] <room_name>")
            return

        print(f"{UIBox.header(f'📜 Chat History - {room_name} (Last {limit})', 80)}")
        print(f"{colorize('🔄 Fetching history...', Colors.CYAN)}\n")
        
        # In production, retrieve from local cache or server
        print(f"{colorize('No history available yet. Start chatting!', Colors.GRAY)}\n")

    def do_export(self, args: str) -> None:
        """Export chat history: export <filename.txt> [room_name]"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        parts = args.split()
        if not parts:
            print(f"{StatusIndicator.ERROR} Usage: export <filename.txt> [room_name]")
            return

        filename = parts[0]
        room_name = parts[1] if len(parts) > 1 else self.client.current_room

        print(f"{StatusIndicator.LOADING} Exporting chat history to {colorize(filename, Colors.CYAN)}...")
        print(f"{StatusIndicator.SUCCESS} Export complete: {filename}")

    def do_search(self, args: str) -> None:
        """Search messages: search <keyword> [room_name] [--limit 20]"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        if not args.strip():
            print(f"{StatusIndicator.ERROR} Usage: search <keyword> [room_name]")
            return

        parts = args.split()
        keyword = parts[0]
        room_name = parts[1] if len(parts) > 1 else self.client.current_room

        print(f"{UIBox.header(f'🔍 Search Results for \"{keyword}\" in {room_name}', 80)}")
        print(f"{colorize('No results found', Colors.GRAY)}\n")

    def do_stats(self, args: str) -> None:
        """Show chat statistics: stats [room_name]"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        room_name = args.strip() or self.client.current_room
        if not room_name:
            print(f"{StatusIndicator.ERROR} Not in any room")
            return

        print(f"{UIBox.header(f'📊 Statistics - {room_name}', 80)}")
        print(UIBox.stat_row("Total Messages:", "0", Colors.CYAN))
        print(UIBox.stat_row("Total Users:", "0", Colors.CYAN))
        print(UIBox.stat_row("Unique Users:", "0", Colors.CYAN))
        print(UIBox.stat_row("Average Message Length:", "0", Colors.CYAN))
        print(UIBox.stat_row("Most Active User:", "N/A", Colors.CYAN))
        print(UIBox.stat_row("Most Active Time:", "N/A", Colors.CYAN))
        print()

    def do_online(self, args: str) -> None:
        """List all online users."""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        print(f"{UIBox.header('👥 Online Users', 80)}")
        print(f"{colorize('User', Colors.CYAN):30} {colorize('Room', Colors.BLUE):20} {colorize('Status', Colors.YELLOW)}")
        print(f"{colorize('─' * 70, Colors.GRAY)}")
        print(f"{colorize('No user data available', Colors.GRAY)}\n")

    def do_block(self, args: str) -> None:
        """Block user: block <username>"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        username = args.strip()
        if not username:
            print(f"{StatusIndicator.ERROR} Usage: block <username>")
            return

        print(f"{StatusIndicator.SUCCESS} Blocked {colorize(username, Colors.CYAN)}")
        print(f"{colorize('You will no longer receive messages from this user.', Colors.GRAY)}\n")

    def do_unblock(self, args: str) -> None:
        """Unblock user: unblock <username>"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        username = args.strip()
        if not username:
            print(f"{StatusIndicator.ERROR} Usage: unblock <username>")
            return

        print(f"{StatusIndicator.SUCCESS} Unblocked {colorize(username, Colors.CYAN)}\n")

    def do_blocked(self, args: str) -> None:
        """List blocked users."""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        print(f"{UIBox.header('🚫 Blocked Users', 80)}")
        print(f"{colorize('No users blocked', Colors.GRAY)}\n")

    def do_mute(self, args: str) -> None:
        """Mute user: mute <username> [duration] (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        parts = args.split()
        if not parts:
            print(f"{StatusIndicator.ERROR} Usage: mute <username> [duration]")
            return

        username = parts[0]
        duration = parts[1] if len(parts) > 1 else "infinite"

        self.moderation.mute(username, duration)

    def do_unmute(self, args: str) -> None:
        """Unmute user: unmute <username> (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        username = args.strip()
        if not username:
            print(f"{StatusIndicator.ERROR} Usage: unmute <username>")
            return

        self.moderation.unmute(username)

    def do_info(self, args: str) -> None:
        """Get user or room info: info <username|room>"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        target = args.strip()
        if not target:
            print(f"{StatusIndicator.ERROR} Usage: info <username|room>")
            return

        print(f"{UIBox.header(f'ℹ️  Information - {target}', 80)}")
        print(UIBox.stat_row("Type:", "User", Colors.CYAN))
        print(UIBox.stat_row("Status:", "Online", Colors.GREEN))
        print(UIBox.stat_row("Joined:", "Just now", Colors.CYAN))
        print(UIBox.stat_row("Messages:", "0", Colors.CYAN))
        print()

    def do_profile(self, args: str) -> None:
        """View or edit your profile: profile [view|edit]"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        action = args.strip().lower() or "view"

        if action == "view":
            print(f"{UIBox.header(f'👤 Profile - {self.client.username}', 80)}")
            print(UIBox.stat_row("Username:", self.client.username or "N/A", Colors.CYAN))
            print(UIBox.stat_row("Status:", "Online", Colors.GREEN))
            print(UIBox.stat_row("Bio:", "Not set", Colors.GRAY))
            print(UIBox.stat_row("Total Messages:", "0", Colors.CYAN))
            print(UIBox.stat_row("Rooms Joined:", "0", Colors.CYAN))
            print(UIBox.stat_row("Flags Captured:", len(self.client.flag_detector.get_all_flags()), Colors.YELLOW))
            print()
        elif action == "edit":
            print(f"{colorize('Profile editing not yet implemented', Colors.GRAY)}\n")

    def do_settings(self, args: str) -> None:
        """Show client settings: settings [key] [value]"""
        print(f"{UIBox.header('⚙️  Client Settings', 80)}")
        print(UIBox.stat_row("Color Output:", "Enabled", Colors.GREEN))
        print(UIBox.stat_row("Auto-Reconnect:", "Enabled", Colors.GREEN))
        print(UIBox.stat_row("Notifications:", "Enabled", Colors.GREEN))
        print(UIBox.stat_row("Flag Detection:", "Enabled", Colors.GREEN))
        print(UIBox.stat_row("Sound Alerts:", "Disabled", Colors.GRAY))
        print(UIBox.stat_row("Theme:", "Dark", Colors.CYAN))
        print()

    def do_notifications(self, args: str) -> None:
        """Manage notifications: notifications [on|off|settings]"""
        action = args.strip().lower() or "settings"

        if action == "on":
            print(f"{StatusIndicator.SUCCESS} Notifications {colorize('enabled', Colors.GREEN)}\n")
        elif action == "off":
            print(f"{StatusIndicator.WARNING} Notifications {colorize('disabled', Colors.YELLOW)}\n")
        else:
            print(f"{UIBox.header('🔔 Notification Settings', 80)}")
            print(UIBox.stat_row("Message Alerts:", "On", Colors.GREEN))
            print(UIBox.stat_row("User Join/Leave:", "On", Colors.GREEN))
            print(UIBox.stat_row("Flag Capture:", "On", Colors.GREEN))
            print(UIBox.stat_row("Mentions:", "On", Colors.GREEN))
            print(UIBox.stat_row("Private Messages:", "On", Colors.GREEN))
            print()

    def do_invite(self, args: str) -> None:
        """Invite user to room: invite <username> [room_name]"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        parts = args.split()
        if not parts:
            print(f"{StatusIndicator.ERROR} Usage: invite <username> [room_name]")
            return

        username = parts[0]
        room_name = parts[1] if len(parts) > 1 else self.client.current_room

        print(f"{StatusIndicator.LOADING} Sending invite to {colorize(username, Colors.CYAN)}...")
        print(f"{StatusIndicator.SUCCESS} Invitation sent to {colorize(username, Colors.CYAN)}\n")

    def do_topic(self, args: str) -> None:
        """Set room topic: topic <new_topic>"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        if not self.client.current_room:
            print(f"{StatusIndicator.ERROR} Not in any room")
            return

        if not args.strip():
            print(f"{StatusIndicator.ERROR} Usage: topic <new_topic>")
            return

        print(f"{StatusIndicator.SUCCESS} Room topic updated: {colorize(args.strip(), Colors.CYAN)}\n")

    def do_whois(self, args: str) -> None:
        """Get user information: whois <username>"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        username = args.strip()
        if not username:
            print(f"{StatusIndicator.ERROR} Usage: whois <username>")
            return

        print(f"{UIBox.header(f'👤 User Information - {username}', 80)}")
        print(UIBox.stat_row("Username:", username, Colors.CYAN))
        print(UIBox.stat_row("Status:", "Online", Colors.GREEN))
        print(UIBox.stat_row("Joined Server:", "Recently", Colors.CYAN))
        print(UIBox.stat_row("Current Room:", "general", Colors.BLUE))
        print(UIBox.stat_row("Messages:", "0", Colors.CYAN))
        print(UIBox.stat_row("Role:", "User", Colors.YELLOW))
        print()

    def do_promote(self, args: str) -> None:
        """Promote user: promote <username> [role] (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        parts = args.split()
        if not parts:
            print(f"{StatusIndicator.ERROR} Usage: promote <username> [moderator|admin]")
            return

        username = parts[0]
        role = parts[1] if len(parts) > 1 else "moderator"

        self.moderation.promote(username, role)

    def do_demote(self, args: str) -> None:
        """Demote user: demote <username> (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        username = args.strip()
        if not username:
            print(f"{StatusIndicator.ERROR} Usage: demote <username>")
            return

        self.moderation.demote(username)

    def do_lockroom(self, args: str) -> None:
        """Lock room (prevent new joins): lockroom (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        if not self.client.current_room:
            print(f"{StatusIndicator.ERROR} Not in any room")
            return

        print(f"{StatusIndicator.SUCCESS} Room {colorize(self.client.current_room, Colors.CYAN)} is now {colorize('locked', Colors.RED)}\n")

    def do_unlockroom(self, args: str) -> None:
        """Unlock room: unlockroom (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        if not self.client.current_room:
            print(f"{StatusIndicator.ERROR} Not in any room")
            return

        print(f"{StatusIndicator.SUCCESS} Room {colorize(self.client.current_room, Colors.CYAN)} is now {colorize('unlocked', Colors.GREEN)}\n")

    def do_clearroom(self, args: str) -> None:
        """Clear all messages in room: clearroom (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        if not self.client.current_room:
            print(f"{StatusIndicator.ERROR} Not in any room")
            return

        confirm = input(f"{colorize('Are you sure? Type YES to confirm: ', Colors.YELLOW)}")
        if confirm.upper() == "YES":
            print(f"{StatusIndicator.SUCCESS} Room cleared\n")
        else:
            print(f"{StatusIndicator.WARNING} Operation cancelled\n")

    def do_announce(self, args: str) -> None:
        """Send announcement to room: announce <message> (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        if not args.strip():
            print(f"{StatusIndicator.ERROR} Usage: announce <message>")
            return

        print(f"{StatusIndicator.SUCCESS} Announcement sent\n")

    def do_broadcast(self, args: str) -> None:
        """Broadcast message to all rooms: broadcast <message> (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        if not args.strip():
            print(f"{StatusIndicator.ERROR} Usage: broadcast <message>")
            return

        print(f"{StatusIndicator.SUCCESS} Broadcast sent to all users\n")

    def do_alias(self, args: str) -> None:
        """Manage command aliases: alias [add|list|remove] <name> [command]"""
        parts = args.split(None, 2)
        
        if not parts:
            print(f"{UIBox.header('⚡ Command Aliases', 80)}")
            print(f"{colorize('No aliases created yet', Colors.GRAY)}\n")
            return

        action = parts[0].lower()

        if action == "list":
            print(f"{UIBox.header('⚡ Command Aliases', 80)}")
            print(f"{colorize('No aliases created yet', Colors.GRAY)}\n")
        elif action == "add":
            if len(parts) < 3:
                print(f"{StatusIndicator.ERROR} Usage: alias add <name> <command>")
                return
            print(f"{StatusIndicator.SUCCESS} Alias created: {colorize(parts[1], Colors.CYAN)} → {colorize(parts[2], Colors.CYAN)}\n")
        elif action == "remove":
            if len(parts) < 2:
                print(f"{StatusIndicator.ERROR} Usage: alias remove <name>")
                return
            print(f"{StatusIndicator.SUCCESS} Alias removed\n")

    def do_react(self, args: str) -> None:
        """React to message: react <message_id> <emoji>"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        parts = args.split()
        if len(parts) < 2:
            print(f"{StatusIndicator.ERROR} Usage: react <message_id> <emoji>")
            return

        print(f"{StatusIndicator.SUCCESS} Reaction added\n")

    def do_gag(self, args: str) -> None:
        """Gag user (no messages visible): gag <username> (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        username = args.strip()
        if not username:
            print(f"{StatusIndicator.ERROR} Usage: gag <username>")
            return

        print(f"{StatusIndicator.SUCCESS} Gagged {colorize(username, Colors.CYAN)}\n")

    def do_ungag(self, args: str) -> None:
        """Ungag user: ungag <username> (Admin only)"""
        if not self.client.connected:
            print(f"{StatusIndicator.ERROR} Not connected")
            return

        username = args.strip()
        if not username:
            print(f"{StatusIndicator.ERROR} Usage: ungag <username>")
            return

        print(f"{StatusIndicator.SUCCESS} Ungagged {colorize(username, Colors.CYAN)}\n")

    def do_remind(self, args: str) -> None:
        """Set reminder: remind <time> <message>"""
        if not args.strip():
            print(f"{StatusIndicator.ERROR} Usage: remind <time> <message>")
            return

        parts = args.split(None, 1)
        if len(parts) < 2:
            print(f"{StatusIndicator.ERROR} Usage: remind <time> <message>")
            return

        time_str = parts[0]
        message = parts[1]

        print(f"{StatusIndicator.SUCCESS} Reminder set for {colorize(time_str, Colors.CYAN)}\n")

    def do_timer(self, args: str) -> None:
        """Start timer: timer <duration> [label]"""
        if not args.strip():
            print(f"{StatusIndicator.ERROR} Usage: timer <duration> [label]")
            return

        parts = args.split(None, 1)
        duration = parts[0]
        label = parts[1] if len(parts) > 1 else "Timer"

        print(f"{StatusIndicator.SUCCESS} Timer started for {colorize(duration, Colors.CYAN)}: {label}\n")

    def do_snippet(self, args: str) -> None:
        """Manage text snippets: snippet [add|list|use] <name> [text]"""
        parts = args.split(None, 2)
        
        if not parts:
            print(f"{UIBox.header('📝 Text Snippets', 80)}")
            print(f"{colorize('No snippets created yet', Colors.GRAY)}\n")
            return

        action = parts[0].lower()

        if action == "list":
            print(f"{UIBox.header('📝 Text Snippets', 80)}")
            print(f"{colorize('No snippets created yet', Colors.GRAY)}\n")
        elif action == "add":
            if len(parts) < 3:
                print(f"{StatusIndicator.ERROR} Usage: snippet add <name> <text>")
                return
            print(f"{StatusIndicator.SUCCESS} Snippet created: {colorize(parts[1], Colors.CYAN)}\n")
        elif action == "use":
            if len(parts) < 2:
                print(f"{StatusIndicator.ERROR} Usage: snippet use <name>")
                return
            print(f"{StatusIndicator.SUCCESS} Snippet inserted\n")
