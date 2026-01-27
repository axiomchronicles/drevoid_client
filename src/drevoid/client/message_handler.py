"""Message handling and display."""

import re
import time
from typing import Callable, List
from ..core.protocol import MessageType, Colors, colorize, format_timestamp, create_message
from ..ctf.flag_detector import FlagDetector
from ..utils.emoji_aliases import EmojiAliases
from ..utils.notifications import NotificationManager


class MessageHandler:
    """
    Processes incoming messages and manages display.

    Handles flag detection, emoji replacement, and various message types.
    """

    def __init__(
        self,
        flag_detector: FlagDetector,
        connection_manager: "ConnectionManager",
        notification_manager: NotificationManager,
    ):
        """
        Initialize message handler.

        Args:
            flag_detector: Flag detector instance
            connection_manager: Connection manager instance
            notification_manager: Notification manager instance
        """
        self.flag_detector = flag_detector
        self.connection_manager = connection_manager
        self.notification_manager = notification_manager
        self.username: str | None = None
        self.callbacks: List[Callable] = []

    def set_username(self, username: str) -> None:
        """Set current username."""
        self.username = username

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to message display events."""
        self.callbacks.append(callback)

    def _display_message(self, text: str) -> None:
        """Display message via subscribers."""
        for callback in self.callbacks:
            callback(text)

    def _highlight_flags(self, content: str) -> str:
        """Highlight flags in content."""
        highlighted = content
        flags = self.flag_detector.detect(content)
        for flag in flags:
            highlighted = highlighted.replace(
                flag,
                f"{colorize(flag, Colors.HIGHLIGHT + Colors.GREEN)}",
            )
        return highlighted

    def handle(self, message: dict, current_room: str) -> None:
        """
        Process incoming message.

        Args:
            message: Message dictionary
            current_room: Current room name
        """
        msg_type = message.get("type")
        data = message.get("data", {})
        timestamp = message.get("timestamp", time.time())
        time_str = format_timestamp(timestamp)

        handlers = {
            MessageType.MESSAGE.value: self._handle_room_message,
            MessageType.PRIVATE_MESSAGE.value: self._handle_private_message,
            MessageType.NOTIFICATION.value: self._handle_notification,
            MessageType.FLAG_RESPONSE.value: self._handle_flag_response,
            MessageType.SUCCESS.value: self._handle_success,
            MessageType.ERROR.value: self._handle_error,
        }

        handler = handlers.get(msg_type)
        if handler:
            handler(data, time_str)

    def _handle_room_message(self, data: dict, time_str: str) -> None:
        """Handle room message."""
        username = data.get("username", "Unknown")
        content = data.get("content", "")
        room = data.get("room", "")

        content = EmojiAliases.replace(content)
        flags = self.flag_detector.detect(content)

        if flags:
            for flag in flags:
                self.flag_detector.store_flag(flag, username, room, content[:50])
                self.notification_manager.notify_flag_found(
                    self.flag_detector.flags_found[flag],
                    username,
                )

                flag_submit_msg = create_message(
                    MessageType.FLAG_SUBMIT,
                    {
                        "content": flag,
                        "finder": username,
                        "room": room,
                        "message_preview": content[:50],
                    },
                )
                self.connection_manager.send_data(flag_submit_msg)

        if username == self.username:
            return

        highlighted_content = self._highlight_flags(content)
        display = (
            f"\n{colorize(f'[{time_str}]', Colors.GRAY)} "
            f"{colorize(f'{username}', Colors.CYAN)} in "
            f"{colorize(f'#{room}', Colors.BLUE)}: {highlighted_content}"
        )
        self._display_message(display)

    def _handle_private_message(self, data: dict, time_str: str) -> None:
        """Handle private message."""
        from_user = data.get("from", "Unknown")
        content = data.get("content", "")
        content = EmojiAliases.replace(content)
        highlighted_content = self._highlight_flags(content)
        display = (
            f"\n{colorize(f'📩 [{time_str}] Private from {from_user}:', Colors.PURPLE)} "
            f"{highlighted_content}"
        )
        self._display_message(display)

    def _handle_notification(self, data: dict, time_str: str) -> None:
        """Handle notification."""
        message_text = data.get("message", "")
        display = f"\n{colorize(f'📢 [{time_str}]', Colors.YELLOW)} {message_text}"
        self._display_message(display)

    def _handle_flag_response(self, data: dict, time_str: str) -> None:
        """Handle flag response."""
        flags = data.get("flags", [])
        if not flags:
            display = f"{colorize('No flags found yet.', Colors.GRAY)}"
            self._display_message(display)
            return

        display = f"\n{colorize('🚩 Captured Flags:', Colors.BOLD + Colors.YELLOW)}"
        self._display_message(display)

        for idx, flag_info in enumerate(flags, 1):
            flag_timestamp = flag_info.get("timestamp", time.time())
            time_str = format_timestamp(flag_timestamp)

            display = f"  {idx}. {colorize(flag_info['content'], Colors.HIGHLIGHT + Colors.GREEN)}"
            self._display_message(display)

            display = (
                f"     Found by: {colorize(flag_info['finder'], Colors.GREEN)} "
                f"in #{colorize(flag_info['room'], Colors.BLUE)}"
            )
            self._display_message(display)

            display = f"     Time: {colorize(time_str, Colors.GRAY)}"
            self._display_message(display)

            display = f"     Context: {flag_info['message_preview'][:60]}..."
            self._display_message(display)

            self._display_message("")

    def _handle_success(self, data: dict, time_str: str) -> None:
        """Handle success response."""
        message_text = data.get("message", "")
        rooms = data.get("rooms", [])
        users = data.get("users", [])
        stats = data.get("stats", {})

        display = f"\n{colorize('✅', Colors.GREEN)} {message_text}"
        self._display_message(display)

        if rooms:
            display = f"\n{colorize('🏠 Available Rooms:', Colors.BOLD)}"
            self._display_message(display)
            for room in rooms:
                protection = "🔒" if room["password_protected"] else "🔓"
                room_type = f"({room['type']})"
                users_info = f"{room['users']}/{room['max_users']}"
                display = (
                    f"  {protection} {colorize(room['name'], Colors.CYAN)} "
                    f"{room_type} - {users_info} users"
                )
                self._display_message(display)

        if users:
            display = f"\n{colorize('👥 Users in room:', Colors.BOLD)}"
            self._display_message(display)
            for user in users:
                is_mod = user["is_moderator"]
                role_color = Colors.RED if user["role"] == "admin" else (Colors.YELLOW if is_mod else Colors.WHITE)
                role_symbol = "👑" if user["role"] == "admin" else ("⭐" if is_mod else "👤")
                display = f"  {role_symbol} {colorize(user['username'], role_color)}"
                self._display_message(display)

        if stats:
            uptime = stats.get("uptime", 0)
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            display = f"\n{colorize('📊 Server Stats:', Colors.BOLD)}"
            self._display_message(display)
            display = f"  Users: {stats.get('connected_users', 0)}"
            self._display_message(display)
            display = f"  Rooms: {stats.get('active_rooms', 0)}"
            self._display_message(display)
            display = f"  Uptime: {hours:02d}:{minutes:02d}"
            self._display_message(display)

    def _handle_error(self, data: dict, time_str: str) -> None:
        """Handle error response."""
        message_text = data.get("message", "")
        display = f"\n{colorize('❌ Error:', Colors.RED)} {message_text}"
        self._display_message(display)
