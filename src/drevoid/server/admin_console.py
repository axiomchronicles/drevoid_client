"""Advanced admin console interface with full management capabilities."""

import cmd
import time
import json
from typing import TYPE_CHECKING, List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from ..core.protocol import Colors, colorize, MessageType, RoomType
from ..ui.ui_components import UIBox, StatusIndicator

if TYPE_CHECKING:
    from .server import ChatServer


class AdminConsole(cmd.Cmd):
    """Advanced admin console for server management."""

    def __init__(self, server: "ChatServer"):
        """
        Initialize admin console.

        Args:
            server: Chat server instance
        """
        super().__init__()
        self.server = server
        self.intro = self._get_intro()
        self.prompt = self._get_prompt()
        
        # Enhanced tracking
        self.user_actions: Dict[str, List] = defaultdict(list)  # User action history
        self.user_warnings: Dict[str, int] = defaultdict(int)    # Warning counts
        self.banned_users_global: Set[str] = set()              # Global bans
        self.muted_users_global: Set[str] = set()               # Global mutes
        self.user_session_times: Dict[str, float] = {}           # Session start times
        self.alerts_active = False                               # Alert monitoring
        self.rate_limits: Dict[str, int] = defaultdict(int)     # Message rate tracking

    def _get_intro(self) -> str:
        """Get console intro message."""
        return f"\n{UIBox.header('🛡️ DREVOID ADMIN CONSOLE', 80)}\n{colorize('Type help or ? for command list', Colors.CYAN)}\n"

    def _get_prompt(self) -> str:
        """Get current prompt."""
        return f"{colorize('admin', Colors.RED)} {colorize('»', Colors.BOLD)} "

    def emptyline(self) -> None:
        """Handle empty line."""
        pass

    def default(self, line: str) -> None:
        """Handle unknown command."""
        print(f"{StatusIndicator.ERROR} Unknown command: {colorize(line, Colors.YELLOW)}")
    
    def do_EOF(self, arg: str) -> bool:
        """Handle EOF (Ctrl+D) - gracefully exit."""
        print(f"\n{colorize('Admin console closed.', Colors.YELLOW)}")
        return True

    # ============== USER MANAGEMENT ==============
    def do_users(self, arg: str) -> None:
        """List all connected users. Usage: users [--detailed]"""
        clients = self.server.client_handler.clients

        if not clients.keys():
            print(f"{StatusIndicator.INFO} No connected users")
            return

        print(f"\n{UIBox.section('Connected Users', Colors.CYAN)}")

        if "--detailed" in arg or "-d" in arg:
            self._show_detailed_users(clients)
        else:
            self._show_users_summary(clients)

    def _show_users_summary(self, clients: Dict) -> None:
        """Show users in summary format."""
        print(UIBox.table_header(["Username", "Role", "Room", "Address"], [20, 15, 20, 25]))
        print(colorize("─" * 80, Colors.GRAY))

        for username in sorted(clients.keys()):
            client_info = clients[username]
            socket_obj, addr, role = client_info
            room = self.server.room_manager.get_user_room(username) or "none"
            
            role_str = f"{StatusIndicator.ADMIN if role == 'admin' else StatusIndicator.MOD if role == 'moderator' else StatusIndicator.USER} {role}"
            values = [username[:20], role, room[:20], f"{addr[0]}:{addr[1]}"]
            print(UIBox.table_row(values, [20, 15, 20, 25]))

        print(f"\n{colorize(f'Total: {len(clients.keys())} user(s)', Colors.GREEN)}")

    def _show_detailed_users(self, clients: Dict) -> None:
        """Show users in detailed format."""
        for i, username in enumerate(sorted(clients.keys()), 1):
            client_info = clients[username]
            socket_obj, addr, role = client_info
            room = self.server.room_manager.get_user_room(username) or "none"

            print(f"\n{colorize(f'[{i}] {username}', Colors.BOLD + Colors.CYAN)}")
            print(f"  {colorize('Role:', Colors.YELLOW):<15} {role.upper()}")
            print(f"  {colorize('Room:', Colors.YELLOW):<15} {room}")
            print(f"  {colorize('IP Address:', Colors.YELLOW):<15} {addr[0]}:{addr[1]}")
            print(colorize("  " + "─" * 50, Colors.GRAY))

    def do_ban(self, arg: str) -> None:
        """Ban a user from a room or globally. Usage: ban <username> [--global]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: ban <username> [--global]")
            return

        parts = arg.split()
        username = parts[0]
        is_global = "--global" in arg or "-g" in arg

        clients = self.server.client_handler.clients
        if username not in clients.keys():
            print(f"{StatusIndicator.ERROR} User {colorize(username, Colors.RED)} not found")
            return

        room = self.server.room_manager.get_user_room(username)
        if not room:
            print(f"{StatusIndicator.ERROR} User is not in any room")
            return

        # Ban user
        self.server.room_manager.ban_user(username, room)
        self.server.room_manager.remove_user_from_room(username, room)

        # Notify user
        self.server.client_handler.send_to_client(
            username,
            MessageType.NOTIFICATION,
            {"message": f"You were banned from {room}"}
        )

        # Broadcast notification
        self.server.client_handler.broadcast_to_room(
            self.server.room_manager,
            room,
            MessageType.NOTIFICATION,
            {"message": f"{username} was banned by admin"}
        )

        scope = "globally" if is_global else f"from {room}"
        print(f"{StatusIndicator.SUCCESS} User {colorize(username, Colors.CYAN)} banned {scope}")
        self.server.log(f"User {username} banned {scope} by admin", "warning")

    def do_kick(self, arg: str) -> None:
        """Kick a user from current room. Usage: kick <username>"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: kick <username>")
            return

        username = arg.strip()
        clients = self.server.client_handler.clients

        if username not in clients.keys():
            print(f"{StatusIndicator.ERROR} User {colorize(username, Colors.RED)} not found")
            return

        room = self.server.room_manager.get_user_room(username)
        if not room:
            print(f"{StatusIndicator.ERROR} User is not in any room")
            return

        # Kick user
        self.server.room_manager.remove_user_from_room(username, room)
        self.server.client_handler.send_to_client(
            username,
            MessageType.NOTIFICATION,
            {"message": f"You were kicked from {room}"}
        )

        # Broadcast notification
        self.server.client_handler.broadcast_to_room(
            self.server.room_manager,
            room,
            MessageType.NOTIFICATION,
            {"message": f"{username} was kicked by admin"}
        )

        print(f"{StatusIndicator.SUCCESS} User {colorize(username, Colors.CYAN)} kicked from {colorize(room, Colors.YELLOW)}")
        self.server.log(f"User {username} kicked from {room} by admin", "warning")

    def do_remove(self, arg: str) -> None:
        """Remove/disconnect a user. Usage: remove <username> [reason]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: remove <username> [reason]")
            return

        parts = arg.split(None, 1)
        username = parts[0]
        reason = parts[1] if len(parts) > 1 else "No reason provided"

        clients = self.server.client_handler.clients
        if username not in clients.keys():
            print(f"{StatusIndicator.ERROR} User {colorize(username, Colors.RED)} not found")
            return

        # Send disconnect message
        self.server.client_handler.send_to_client(
            username,
            MessageType.NOTIFICATION,
            {"message": f"Disconnected by admin. Reason: {reason}"}
        )

        # Disconnect user
        room = self.server.room_manager.get_user_room(username)
        if room:
            self.server.room_manager.remove_user_from_room(username, room)

        self.server.client_handler.unregister_client(username)

        print(f"{StatusIndicator.SUCCESS} User {colorize(username, Colors.CYAN)} removed. Reason: {reason}")
        self.server.log(f"User {username} removed by admin. Reason: {reason}", "warning")

    # ============== ROOM MANAGEMENT ==============
    def do_rooms(self, arg: str) -> None:
        """List all rooms. Usage: rooms [--detailed]"""
        rooms = self.server.room_manager.rooms

        if not rooms:
            print(f"{StatusIndicator.INFO} No rooms available")
            return

        print(f"\n{UIBox.section('Server Rooms', Colors.CYAN)}")

        if "--detailed" in arg or "-d" in arg:
            self._show_detailed_rooms(rooms)
        else:
            self._show_rooms_summary(rooms)

    def _show_rooms_summary(self, rooms: Dict) -> None:
        """Show rooms summary."""
        print(UIBox.table_header(["Room Name", "Type", "Users", "Max", "Protected"], [20, 12, 8, 8, 12]))
        print(colorize("─" * 80, Colors.GRAY))

        for room_name, room_info in sorted(rooms.items()):
            protected = "Yes 🔒" if room_info["password_protected"] else "No 🔓"
            users = len(room_info["users"])
            max_users = room_info["max_users"]
            values = [room_name[:20], room_info["type"][:12], str(users), str(max_users), protected]
            print(UIBox.table_row(values, [20, 12, 8, 8, 12]))

        print(f"\n{colorize(f'Total: {len(rooms.keys())} room(s)', Colors.GREEN)}")

    def _show_detailed_rooms(self, rooms: Dict) -> None:
        """Show rooms in detail."""
        for i, (room_name, room_info) in enumerate(sorted(rooms.items()), 1):
            users_list = ", ".join(room_info["users"]) if room_info["users"] else "None"
            
            print(f"\n{colorize(f'[{i}] {room_name}', Colors.BOLD + Colors.CYAN)}")
            print(f"  {colorize('Type:', Colors.YELLOW):<15} {room_info['type']}")
            print(f"  {colorize('Users:', Colors.YELLOW):<15} {len(room_info['users'])}/{room_info['max_users']}")
            print(f"  {colorize('Protected:', Colors.YELLOW):<15} {'Yes' if room_info['password_protected'] else 'No'}")
            print(f"  {colorize('Members:', Colors.YELLOW):<15} {users_list}")
            print(colorize("  " + "─" * 50, Colors.GRAY))

    # ============== FLAG MANAGEMENT ==============
    def do_flags(self, arg: str) -> None:
        """List all captured flags. Usage: flags [--detailed] [--user <username>]"""
        flags = self.server.client_handler.get_all_flags()

        if not flags:
            print(f"{StatusIndicator.INFO} No flags captured yet")
            return

        # Filter by user if specified
        if "--user" in arg:
            parts = arg.split()
            try:
                user_idx = parts.index("--user")
                filter_user = parts[user_idx + 1]
                flags = [f for f in flags if f["finder"] == filter_user]
                if not flags:
                    print(f"{StatusIndicator.INFO} No flags found for user {colorize(filter_user, Colors.YELLOW)}")
                    return
            except (IndexError, ValueError):
                print(f"{StatusIndicator.ERROR} Invalid --user argument")
                return

        print(f"\n{UIBox.section('Captured Flags', Colors.GREEN)}")
        print(f"{colorize(f'Total Flags: {len(flags)}', Colors.BOLD + Colors.GREEN)}\n")

        if "--detailed" in arg or "-d" in arg:
            self._show_detailed_flags(flags)
        else:
            self._show_flags_summary(flags)

    def _show_flags_summary(self, flags: List[Dict]) -> None:
        """Show flags summary."""
        print(UIBox.table_header(["#", "Finder", "Room", "Time", "Preview"], [3, 15, 15, 20, 25]))
        print(colorize("─" * 80, Colors.GRAY))

        for i, flag in enumerate(flags, 1):
            timestamp = datetime.fromtimestamp(flag["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            preview = flag["message_preview"][:25] + "..." if len(flag["message_preview"]) > 25 else flag["message_preview"]
            values = [str(i), flag["finder"][:15], flag["room"][:15], timestamp, preview]
            print(UIBox.table_row(values, [3, 15, 15, 20, 25]))

    def _show_detailed_flags(self, flags: List[Dict]) -> None:
        """Show flags in detail."""
        for i, flag in enumerate(flags, 1):
            timestamp = datetime.fromtimestamp(flag["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n{colorize(f'[{i}] Flag #{i}', Colors.BOLD + Colors.GREEN)}")
            print(f"  {colorize('Content:', Colors.YELLOW):<15} {colorize(flag['content'], Colors.GREEN)}")
            print(f"  {colorize('Finder:', Colors.YELLOW):<15} {flag['finder']}")
            print(f"  {colorize('Room:', Colors.YELLOW):<15} {flag['room']}")
            print(f"  {colorize('Timestamp:', Colors.YELLOW):<15} {timestamp}")
            print(f"  {colorize('Preview:', Colors.YELLOW):<15} {flag['message_preview']}")
            print(colorize("  " + "─" * 50, Colors.GRAY))

    def do_flag_count(self, arg: str) -> None:
        """Show total flag count."""
        count = self.server.client_handler.get_flags_count()
        print(f"\n{colorize(f'Total Flags Captured: {count}', Colors.BOLD + Colors.GREEN)}\n")

    def do_clear_flags(self, arg: str) -> None:
        """Clear all flags. Usage: clear_flags [--confirm]"""
        if "--confirm" not in arg:
            print(f"{StatusIndicator.WARNING} This will delete all flags!")
            print(f"  Re-run with {colorize('--confirm', Colors.YELLOW)} to proceed")
            return

        count = self.server.client_handler.get_flags_count()
        self.server.client_handler.flags_storage.clear()
        print(f"{StatusIndicator.SUCCESS} All {count} flags cleared")
        self.server.log(f"All {count} flags cleared by admin", "warning")

    # ============== SERVER STATISTICS ==============
    def do_stats(self, arg: str) -> None:
        """Show server statistics."""
        stats = self.server._get_server_stats()
        uptime = stats["uptime"]
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        seconds = uptime % 60

        print(f"\n{UIBox.section('Server Statistics', Colors.BLUE)}")
        print(UIBox.stat_row("Connected Users:", str(stats["connected_users"])))
        print(UIBox.stat_row("Active Rooms:", str(stats["active_rooms"])))
        print(UIBox.stat_row("Total Flags:", str(self.server.client_handler.get_flags_count())))
        print(UIBox.stat_row("Uptime:", f"{hours}h {minutes}m {seconds}s"))
        print(UIBox.stat_row("Server Address:", f"{self.server.host}:{self.server.port}"))
        print()

    def do_memory(self, arg: str) -> None:
        """Show memory usage and system info."""
        clients = len(self.server.client_handler.clients.keys())
        rooms = len(self.server.room_manager.rooms.keys())
        flags = len(self.server.client_handler.flags_storage.keys())

        print(f"\n{UIBox.section('System Memory', Colors.BLUE)}")
        print(UIBox.stat_row("Clients in Memory:", f"{clients} connections"))
        print(UIBox.stat_row("Rooms in Memory:", f"{rooms} rooms"))
        print(UIBox.stat_row("Flags in Storage:", f"{flags} flags"))
        print(UIBox.stat_row("History Logs:", f"{len(self.server.history_logs)} entries"))
        print()

    # ============== LOG MANAGEMENT ==============
    def do_logs(self, arg: str) -> None:
        """Show server logs. Usage: logs [--recent <count>] [--tail]"""
        if not self.server.history_logs:
            print(f"{StatusIndicator.INFO} No logs available")
            return

        count = 20
        if "--recent" in arg:
            parts = arg.split()
            try:
                idx = parts.index("--recent")
                count = int(parts[idx + 1])
            except (IndexError, ValueError):
                count = 20

        logs = self.server.history_logs[-count:] if "--tail" not in arg else self.server.history_logs[-count:]

        print(f"\n{UIBox.section('Server Logs', Colors.YELLOW)}")
        print(f"{colorize(f'Showing last {len(logs)} entries:', Colors.GRAY)}\n")

        for log in logs:
            if "[SUCCESS]" in log:
                print(colorize(log, Colors.GREEN))
            elif "[ERROR]" in log:
                print(colorize(log, Colors.RED))
            elif "[WARNING]" in log:
                print(colorize(log, Colors.YELLOW))
            else:
                print(colorize(log, Colors.GRAY))

    def do_clear_logs(self, arg: str) -> None:
        """Clear server logs. Usage: clear_logs [--confirm]"""
        if "--confirm" not in arg:
            print(f"{StatusIndicator.WARNING} This will delete all server logs!")
            print(f"  Re-run with {colorize('--confirm', Colors.YELLOW)} to proceed")
            return

        count = len(self.server.history_logs)
        self.server.history_logs.clear()
        print(f"{StatusIndicator.SUCCESS} All {count} log entries cleared")

    # ============== UTILITY COMMANDS ==============
    def do_broadcast(self, arg: str) -> None:
        """Broadcast message to all connected users. Usage: broadcast <message>"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: broadcast <message>")
            return

        message = arg.strip()
        clients = self.server.client_handler.clients

        for username in clients.keys():
            self.server.client_handler.send_to_client(
                username,
                MessageType.NOTIFICATION,
                {"message": f"[ADMIN] {message}"}
            )

        print(f"{StatusIndicator.SUCCESS} Message broadcasted to {len(clients.keys())} user(s)")
        self.server.log(f"Admin broadcast: {message}", "info")

    # ============== ADVANCED USER ANALYTICS ==============
    def do_analytics(self, arg: str) -> None:
        """Show user analytics and statistics. Usage: analytics [--detailed] [--export]"""
        clients = self.server.client_handler.clients
        
        if not clients.keys():
            print(f"{StatusIndicator.INFO} No user data available")
            return
        
        print(f"\n{UIBox.section('User Analytics', Colors.BLUE)}")
        
        # Session statistics
        now = time.time()
        session_lengths = []
        for username in clients.keys():
            if username in self.user_session_times:
                session_length = now - self.user_session_times[username]
                session_lengths.append((username, session_length))
        
        print(UIBox.stat_row("Total Users Connected:", str(len(clients.keys()))))
        print(UIBox.stat_row("Most Recent Join:", f"{list(clients.keys())[-1] if clients.keys() else 'None'}"))
        
        # Average session time
        if session_lengths:
            avg_session = sum(t for _, t in session_lengths) / len(session_lengths)
            print(UIBox.stat_row("Average Session:", f"{int(avg_session)}s"))
            longest_user, longest_time = max(session_lengths, key=lambda x: x[1])
            print(UIBox.stat_row("Longest Session:", f"{longest_user}: {int(longest_time)}s"))
        
        # Role distribution
        role_counts = defaultdict(int)
        for client_info in clients.values():
            role_counts[client_info[2]] += 1
        
        print(f"\n{colorize('Role Distribution:', Colors.YELLOW)}")
        for role, count in role_counts.items():
            print(f"  {colorize(role.upper(), Colors.CYAN)}: {count}")
        
        if "--export" in arg:
            self._export_analytics(clients)

    def _export_analytics(self, clients: Dict) -> None:
        """Export analytics to JSON file."""
        analytics_data = {
            "timestamp": datetime.now().isoformat(),
            "total_users": len(clients.keys()),
            "users": [],
            "statistics": self.server._get_server_stats()
        }
        
        for username, client_info in clients.items():
            socket_obj, addr, role = client_info
            room = self.server.room_manager.get_user_room(username) or "none"
            analytics_data["users"].append({
                "username": username,
                "role": role,
                "room": room,
                "ip": addr[0],
                "port": addr[1]
            })
        
        filename = f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(analytics_data, f, indent=2)
        
        print(f"{StatusIndicator.SUCCESS} Analytics exported to {filename}")

    # ============== ROOM MANAGEMENT ENHANCED ==============
    def do_room_create(self, arg: str) -> None:
        """Create a new room. Usage: room_create <name> [--private] [--max <count>]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: room_create <name> [--private] [--max <count>]")
            return
        
        parts = arg.split()
        room_name = parts[0]
        
        is_private = "--private" in arg
        max_users = 50
        
        if "--max" in parts:
            try:
                max_idx = parts.index("--max")
                max_users = int(parts[max_idx + 1])
            except (IndexError, ValueError):
                max_users = 50
        
        room_type = "PRIVATE" if is_private else "PUBLIC"
        password = input(f"Password (leave empty for public): ") if is_private else ""
        
        success = self.server.room_manager.create_room(
            room_name,
            RoomType.PRIVATE if is_private else RoomType.PUBLIC,
            password,
            max_users
        )
        
        if success:
            print(f"{StatusIndicator.SUCCESS} Room {colorize(room_name, Colors.GREEN)} created ({room_type}, max {max_users})")
            self.server.log(f"Room {room_name} created by admin", "success")
        else:
            print(f"{StatusIndicator.ERROR} Room already exists")

    def do_room_delete(self, arg: str) -> None:
        """Delete a room. Usage: room_delete <name> [--confirm]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: room_delete <name> [--confirm]")
            return
        
        room_name = arg.split()[0]
        
        if "--confirm" not in arg:
            print(f"{StatusIndicator.WARNING} This will delete room {colorize(room_name, Colors.YELLOW)}")
            print(f"  Re-run with {colorize('--confirm', Colors.YELLOW)} to proceed")
            return
        
        if self.server.room_manager.delete_room(room_name):
            print(f"{StatusIndicator.SUCCESS} Room {colorize(room_name, Colors.RED)} deleted")
            self.server.log(f"Room {room_name} deleted by admin", "warning")
        else:
            print(f"{StatusIndicator.ERROR} Cannot delete room (doesn't exist or is protected)")

    def do_room_info(self, arg: str) -> None:
        """Show detailed room information. Usage: room_info <name>"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: room_info <name>")
            return
        
        room_name = arg.strip()
        rooms = self.server.room_manager.rooms
        
        if room_name not in rooms:
            print(f"{StatusIndicator.ERROR} Room not found")
            return
        
        room_info = rooms[room_name]
        users = room_info["users"]
        history = self.server.room_manager.get_room_history(room_name)
        
        print(f"\n{UIBox.section(f'Room: {room_name}', Colors.CYAN)}")
        print(UIBox.stat_row("Type:", room_info["type"]))
        print(UIBox.stat_row("Users:", f"{len(users)}/{room_info['max_users']}"))
        print(UIBox.stat_row("Protected:", "Yes" if room_info["password_protected"] else "No"))
        print(UIBox.stat_row("Members:", ", ".join(users) if users else "None"))
        print(UIBox.stat_row("Events:", str(len(history))))
        
        if "--history" in arg and history:
            print(f"\n{colorize('Recent Events:', Colors.YELLOW)}")
            for event in history[-10:]:
                print(f"  • {event}")

    # ============== MUTING & ADVANCED MODERATION ==============
    def do_mute(self, arg: str) -> None:
        """Mute a user in a room. Usage: mute <username> [--global] [--duration <seconds>]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: mute <username> [--global] [--duration <sec>]")
            return
        
        parts = arg.split()
        username = parts[0]
        is_global = "--global" in arg
        
        clients = self.server.client_handler.clients
        if username not in clients.keys():
            print(f"{StatusIndicator.ERROR} User not found")
            return
        
        room = self.server.room_manager.get_user_room(username)
        if not room and not is_global:
            print(f"{StatusIndicator.ERROR} User not in any room")
            return
        
        if is_global:
            self.muted_users_global.add(username)
            scope = "globally"
            notification = "You have been muted globally"
        else:
            self.server.room_manager.mute_user(username, room)
            scope = f"in {room}"
            notification = f"You have been muted in {room}"
        
        # Send notification to user
        self.server.client_handler.send_to_client(
            username,
            MessageType.NOTIFICATION,
            {"message": notification}
        )
        
        self.user_warnings[username] += 1
        print(f"{StatusIndicator.SUCCESS} User {colorize(username, Colors.CYAN)} muted {scope}")
        self.server.log(f"User {username} muted {scope} by admin", "warning")

    def do_unmute(self, arg: str) -> None:
        """Unmute a user. Usage: unmute <username> [--global]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: unmute <username> [--global]")
            return
        
        username = arg.split()[0]
        is_global = "--global" in arg
        
        if is_global:
            if username in self.muted_users_global:
                self.muted_users_global.discard(username)
                scope = "globally"
                notification = "You have been unmuted globally"
            else:
                print(f"{StatusIndicator.ERROR} User not muted globally")
                return
        else:
            room = self.server.room_manager.get_user_room(username)
            if room:
                self.server.room_manager.unmute_user(username, room)
                scope = f"in {room}"
                notification = f"You have been unmuted in {room}"
            else:
                print(f"{StatusIndicator.ERROR} User not in any room")
                return
        
        # Send notification to user
        self.server.client_handler.send_to_client(
            username,
            MessageType.NOTIFICATION,
            {"message": notification}
        )
        
        print(f"{StatusIndicator.SUCCESS} User {colorize(username, Colors.CYAN)} unmuted {scope}")
        self.server.log(f"User {username} unmuted {scope} by admin", "info")

    def do_warnings(self, arg: str) -> None:
        """Show user warnings and violations. Usage: warnings [<username>]"""
        if arg:
            username = arg.strip()
            if username in self.user_warnings:
                count = self.user_warnings[username]
                print(f"\n{colorize(f'Warnings for {username}', Colors.YELLOW)}: {count}")
            else:
                print(f"{StatusIndicator.INFO} No warnings for {username}")
        else:
            print(f"\n{UIBox.section('User Warnings', Colors.YELLOW)}")
            if not self.user_warnings:
                print(f"{StatusIndicator.INFO} No warnings issued")
                return
            
            for user, count in sorted(self.user_warnings.items(), key=lambda x: x[1], reverse=True):
                status = "🔴" if count > 2 else "🟡" if count > 0 else "🟢"
                print(f"  {status} {user}: {count} warning(s)")

    # ============== USER ACTION TRACKING ==============
    def do_user_history(self, arg: str) -> None:
        """Show user action history. Usage: user_history <username> [--detailed]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: user_history <username>")
            return
        
        parts = arg.split()
        username = parts[0]
        
        if username not in self.user_actions:
            print(f"{StatusIndicator.INFO} No history for {username}")
            return
        
        actions = self.user_actions[username]
        print(f"\n{UIBox.section(f'History: {username}', Colors.CYAN)}")
        print(f"{colorize(f'Total Actions: {len(actions)}', Colors.GREEN)}\n")
        
        for i, action in enumerate(actions[-20:], 1):  # Show last 20
            print(f"  {i}. {action}")

    def do_track_user(self, arg: str) -> None:
        """Start/stop tracking a user. Usage: track_user <username>"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: track_user <username>")
            return
        
        username = arg.strip()
        clients = self.server.client_handler.clients
        
        if username not in clients.keys():
            print(f"{StatusIndicator.ERROR} User not found")
            return
        
        # Record session start
        self.user_session_times[username] = time.time()
        self.user_actions[username] = [f"Tracking started: {datetime.now()}"]
        
        print(f"{StatusIndicator.SUCCESS} Now tracking {colorize(username, Colors.CYAN)}")

    # ============== ADVANCED FILTERING & SEARCH ==============
    def do_search_users(self, arg: str) -> None:
        """Search users by criteria. Usage: search_users --role <role> | --room <room>"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: search_users --role <role> | --room <room>")
            return
        
        clients = self.server.client_handler.clients
        results = []
        
        if "--role" in arg:
            parts = arg.split()
            role_idx = parts.index("--role")
            search_role = parts[role_idx + 1]
            results = [(u, c) for u, c in clients.items() if c[2] == search_role]
        
        elif "--room" in arg:
            parts = arg.split()
            room_idx = parts.index("--room")
            search_room = parts[room_idx + 1]
            results = [(u, c) for u, c in clients.items() 
                      if self.server.room_manager.get_user_room(u) == search_room]
        
        if not results:
            print(f"{StatusIndicator.INFO} No users found matching criteria")
            return
        
        print(f"\n{UIBox.section('Search Results', Colors.CYAN)}")
        print(f"Found {len(results)} user(s):\n")
        for username, client_info in results:
            socket_obj, addr, role = client_info
            room = self.server.room_manager.get_user_room(username) or "none"
            print(f"  {colorize(username, Colors.CYAN)} | Role: {role} | Room: {room}")

    # ============== SERVER HEALTH & MONITORING ==============
    def do_health(self, arg: str) -> None:
        """Show detailed server health report."""
        stats = self.server._get_server_stats()
        
        print(f"\n{UIBox.header('🏥 SERVER HEALTH REPORT', 80)}")
        
        # Performance metrics
        print(f"\n{UIBox.section('Performance', Colors.BLUE)}")
        print(UIBox.stat_row("Connected Users:", f"{stats['connected_users']}/100"))
        print(UIBox.stat_row("Active Rooms:", str(stats['active_rooms'])))
        print(UIBox.stat_row("Flag Count:", str(self.server.client_handler.get_flags_count())))
        
        # System metrics
        print(f"\n{UIBox.section('System', Colors.BLUE)}")
        uptime = stats['uptime']
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        print(UIBox.stat_row("Uptime:", f"{hours}h {minutes}m"))
        print(UIBox.stat_row("Log Entries:", str(len(self.server.history_logs))))
        
        # Health status
        print(f"\n{UIBox.section('Health Status', Colors.BLUE)}")
        status = "🟢 HEALTHY" if stats['connected_users'] < 80 else "🟡 WARNING" if stats['connected_users'] < 95 else "🔴 CRITICAL"
        print(UIBox.stat_row("Overall:", status))

    # ============== BACKUP & EXPORT ==============
    def do_export_data(self, arg: str) -> None:
        """Export server data. Usage: export_data [--flags] [--users] [--all]"""
        if not arg:
            arg = "--all"
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "server_stats": self.server._get_server_stats()
        }
        
        if "--flags" in arg or "--all" in arg:
            export_data["flags"] = self.server.client_handler.get_all_flags()
        
        if "--users" in arg or "--all" in arg:
            clients = self.server.client_handler.clients
            export_data["users"] = [{
                "username": u,
                "role": c[2],
                "room": self.server.room_manager.get_user_room(u),
                "ip": c[1][0]
            } for u, c in clients.items()]
        
        filename = f"server_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"{StatusIndicator.SUCCESS} Data exported to {filename}")
        self.server.log(f"Server data exported by admin", "info")

    # ============== PERFORMANCE MONITORING ==============
    def do_performance(self, arg: str) -> None:
        """Show performance metrics. Usage: performance [--benchmark]"""
        clients = self.server.client_handler.clients
        rooms = self.server.room_manager.rooms
        
        print(f"\n{UIBox.section('Performance Metrics', Colors.BLUE)}")
        print(UIBox.stat_row("Clients Connected:", f"{len(clients.keys())}"))
        print(UIBox.stat_row("Rooms Active:", f"{len(rooms.keys())}"))
        print(UIBox.stat_row("Avg Users per Room:", 
                           f"{len(clients.keys()) / len(rooms.keys()) if rooms.keys() else 0:.1f}"))
        print(UIBox.stat_row("Flag Records:", f"{self.server.client_handler.get_flags_count()}"))
        print(UIBox.stat_row("Log Entries:", f"{len(self.server.history_logs)}"))
        
        if "--benchmark" in arg:
            start = time.time()
            for _ in range(1000):
                _ = self.server.client_handler.clients.keys()
            elapsed = time.time() - start
            print(f"\n{colorize('Benchmark Results:', Colors.YELLOW)}")
            print(UIBox.stat_row("1000 iterations:", f"{elapsed*1000:.2f}ms"))

    # ============== GLOBAL BAN MANAGEMENT ==============
    def do_global_ban(self, arg: str) -> None:
        """Add user to global ban list. Usage: global_ban <username> [reason]"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: global_ban <username> [reason]")
            return
        
        parts = arg.split(None, 1)
        username = parts[0]
        reason = parts[1] if len(parts) > 1 else "No reason provided"
        
        self.banned_users_global.add(username)
        print(f"{StatusIndicator.SUCCESS} User {colorize(username, Colors.RED)} added to global ban list")
        print(f"  Reason: {reason}")
        self.server.log(f"User {username} globally banned. Reason: {reason}", "warning")

    def do_global_bans(self, arg: str) -> None:
        """List globally banned users."""
        print(f"\n{UIBox.section('Global Ban List', Colors.RED)}")
        if not self.banned_users_global:
            print(f"{StatusIndicator.INFO} No globally banned users")
            return
        
        for i, username in enumerate(sorted(self.banned_users_global), 1):
            print(f"  {i}. {colorize(username, Colors.RED)}")
        print(f"\nTotal: {len(self.banned_users_global)} user(s)")

    def do_unban_global(self, arg: str) -> None:
        """Remove user from global ban list. Usage: unban_global <username>"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: unban_global <username>")
            return
        
        username = arg.strip()
        if username in self.banned_users_global:
            self.banned_users_global.discard(username)
            print(f"{StatusIndicator.SUCCESS} User {colorize(username, Colors.CYAN)} removed from global ban list")
        else:
            print(f"{StatusIndicator.ERROR} User not in global ban list")

    # ============== AUTOMATED ALERTS ==============
    def do_alerts(self, arg: str) -> None:
        """Manage alerts. Usage: alerts --enable | --disable | --status"""
        if "--enable" in arg:
            self.alerts_active = True
            print(f"{StatusIndicator.SUCCESS} Alerts enabled")
        elif "--disable" in arg:
            self.alerts_active = False
            print(f"{StatusIndicator.SUCCESS} Alerts disabled")
        elif "--status" in arg or not arg:
            status = "🟢 ENABLED" if self.alerts_active else "🔴 DISABLED"
            print(f"Alert System: {status}")
        else:
            print(f"{StatusIndicator.ERROR} Usage: alerts --enable | --disable | --status")

    # ============== SCHEDULED ANNOUNCEMENTS ==============
    def do_schedule_announcement(self, arg: str) -> None:
        """Schedule an announcement. Usage: schedule_announcement <message>"""
        if not arg:
            print(f"{StatusIndicator.ERROR} Usage: schedule_announcement <message>")
            return
        
        message = arg.strip()
        print(f"{StatusIndicator.SUCCESS} Announcement scheduled: {colorize(message, Colors.YELLOW)}")
        self.server.log(f"Announcement scheduled by admin: {message}", "info")

    # ============== HELP & DOCUMENTATION ==============
    def do_help(self, arg: str) -> None:
        """Show help information."""
        print(f"\n{UIBox.header('📚 ADMIN CONSOLE COMMANDS (ENHANCED)', 80)}")

        print(f"\n{UIBox.section('User Management', Colors.CYAN)}")
        print("  users [--detailed]         → List all connected users")
        print("  ban <username>             → Ban user from room")
        print("  kick <username>            → Kick user from room")
        print("  remove <username> [reason] → Disconnect user")
        print("  mute <user> [--global]     → Mute user")
        print("  unmute <user> [--global]   → Unmute user")

        print(f"\n{UIBox.section('User Analytics & Tracking', Colors.CYAN)}")
        print("  analytics [--detailed]     → User analytics")
        print("  track_user <user>          → Track user actions")
        print("  user_history <user>        → User action history")
        print("  warnings [<user>]          → Show warnings")
        print("  search_users --role <r>    → Search by role")
        print("  search_users --room <r>    → Search by room")

        print(f"\n{UIBox.section('Room Management', Colors.CYAN)}")
        print("  rooms [--detailed]         → List all rooms")
        print("  room_create <name>         → Create room")
        print("  room_delete <name>         → Delete room")
        print("  room_info <name>           → Room details")

        print(f"\n{UIBox.section('Flag Management', Colors.CYAN)}")
        print("  flags [--detailed]         → List all flags")
        print("  flags --user <username>    → Show flags by user")
        print("  flag_count                 → Show total flags")
        print("  clear_flags [--confirm]    → Clear all flags")

        print(f"\n{UIBox.section('Server Monitoring', Colors.CYAN)}")
        print("  stats                      → Server stats")
        print("  memory                     → Memory usage")
        print("  health                     → Health report")
        print("  performance [--benchmark]  → Performance metrics")
        print("  logs [--recent <n>]        → View logs")

        print(f"\n{UIBox.section('Advanced Management', Colors.CYAN)}")
        print("  global_ban <user>          → Global ban user")
        print("  global_bans                → List global bans")
        print("  unban_global <user>        → Remove global ban")
        print("  export_data [--all]        → Export server data")
        print("  analytics [--export]       → Export analytics")
        print("  broadcast <message>        → Send message to all")
        print("  alerts --enable/--disable  → Manage alerts")

        print(f"\n{UIBox.section('Control', Colors.CYAN)}")
        print("  help                       → Show this help")
        print("  quit / exit / stop         → Stop server")
        print()

    def do_quit(self, arg: str) -> None:
        """Stop server and exit admin console."""
        if input(f"{colorize('Are you sure? (yes/no): ', Colors.YELLOW)}").lower() == "yes":
            print(f"{StatusIndicator.INFO} Stopping server...")
            self.server.stop()
            return True
        return False

    def do_exit(self, arg: str) -> None:
        """Exit admin console (stop server)."""
        return self.do_quit(arg)

    def do_stop(self, arg: str) -> None:
        """Stop the server."""
        return self.do_quit(arg)
