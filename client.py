import socket
import threading
import cmd
import json
import time
import sys
import os
import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol import *
from notification import NotificationManager
from emojis import EmojiAliasesInstance as EmojiAliases

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    HIGHLIGHT = '\033[7m'
    RESET = '\033[0m'


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{Colors.RESET}"


def format_timestamp(timestamp: float) -> str:
    return time.strftime('%H:%M:%S', time.localtime(timestamp))


class FlagPattern(Enum):
    BRACE_FLAG = r'flag\{[^}]+\}'
    BRACE_FLAG_UPPER = r'FLAG\{[^}]+\}'
    BRACE_CTF = r'CTF\{[^}]+\}'
    BRACE_CTF_LOWER = r'ctf\{[^}]+\}'
    COLON_FLAG = r'flag:[A-Za-z0-9_\-]+'
    COLON_FLAG_UPPER = r'FLAG:[A-Za-z0-9_\-]+'
    MD5_HASH = r'[a-f0-9]{32}(?![a-f0-9])'
    SHA1_HASH = r'[a-f0-9]{40}(?![a-f0-9])'
    SHA256_HASH = r'[a-f0-9]{64}(?![a-f0-9])'


@dataclass
class Flag:
    content: str
    finder: str
    room: str
    timestamp: float
    message_preview: str


class FlagDetector:
    def __init__(self):
        self.flags_found: Dict[str, Flag] = {}
        self.patterns = [pattern.value for pattern in FlagPattern]

    def detect(self, content: str) -> List[str]:
        matches = []
        for pattern in self.patterns:
            found = re.findall(pattern, content, re.IGNORECASE)
            matches.extend(found)
        return list(set(matches))

    def store_flag(self, flag_content: str, finder: str, room: str, message_preview: str):
        if flag_content not in self.flags_found:
            self.flags_found[flag_content] = Flag(
                content=flag_content,
                finder=finder,
                room=room,
                timestamp=time.time(),
                message_preview=message_preview
            )
            return True
        return False

    def get_all_flags(self) -> List[Flag]:
        return list(self.flags_found.values())


class MessageBuffer:
    def __init__(self):
        self.buffer = b''

    def add_data(self, data: bytes):
        self.buffer += data

    def get_message(self) -> Tuple[Optional[dict], bool]:
        message, self.buffer = deserialize_message(self.buffer)
        return message, message is not None

    def is_empty(self) -> bool:
        return len(self.buffer) == 0

class ConnectionManager:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.username = None

    def connect(self, host: str, port: int) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            return True
        except Exception as e:
            print(f"{colorize('❌ Connection failed:', Colors.RED)} {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.connected and self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.connected = False

    def send_data(self, message: dict) -> bool:
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
        if not self.connected:
            return None
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                return None
            return data
        except Exception as e:
            if self.connected:
                print(f"{colorize('❌ Receive error:', Colors.RED)} {e}")
            return None


class RoomManager:
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.current_room = None

    def join(self, room_name: str, password: str = "") -> bool:
        message = create_message(MessageType.JOIN_ROOM, {
            "room_name": room_name,
            "password": password
        })
        if self.connection_manager.send_data(message):
            self.current_room = room_name
            return True
        return False

    def leave(self) -> bool:
        if not self.current_room:
            return False
        message = create_message(MessageType.LEAVE_ROOM, {})
        if self.connection_manager.send_data(message):
            self.current_room = None
            return True
        return False

    def create(self, room_name: str, room_type: str = "public", password: str = "") -> bool:
        message = create_message(MessageType.CREATE_ROOM, {
            "room_name": room_name,
            "room_type": room_type,
            "password": password
        })
        return self.connection_manager.send_data(message)

    def list_rooms(self) -> bool:
        message = create_message(MessageType.LIST_ROOMS, {})
        return self.connection_manager.send_data(message)

    def list_users(self) -> bool:
        message = create_message(MessageType.LIST_USERS, {})
        return self.connection_manager.send_data(message)


class MessageHandler:
    def __init__(self, flag_detector: FlagDetector, connection_manager: ConnectionManager, notification_manager: NotificationManager):
        self.flag_detector = flag_detector
        self.connection_manager = connection_manager
        self.notification_manager = notification_manager
        self.username = None
        self.callbacks: List[callable] = []

    def set_username(self, username: str):
        self.username = username

    def subscribe(self, callback: callable):
        self.callbacks.append(callback)

    def _display_message(self, text: str):
        for callback in self.callbacks:
            callback(text)

    def _highlight_flags(self, content: str) -> str:
        highlighted = content
        flags = self.flag_detector.detect(content)
        for flag in flags:
            highlighted = highlighted.replace(
                flag,
                f"{colorize(flag, Colors.HIGHLIGHT + Colors.GREEN)}"
            )
        return highlighted

    def handle(self, message: dict, current_room: str):
        msg_type = message.get("type")
        data = message.get("data", {})
        timestamp = message.get("timestamp", time.time())
        time_str = format_timestamp(timestamp)

        if msg_type == MessageType.MESSAGE.value:
            self._handle_room_message(data, time_str)
        elif msg_type == MessageType.PRIVATE_MESSAGE.value:
            self._handle_private_message(data, time_str)
        elif msg_type == MessageType.NOTIFICATION.value:
            self._handle_notification(data, time_str)
        elif msg_type == MessageType.FLAG_RESPONSE.value:  
            self._handle_flag_response(data, time_str)
        elif msg_type == MessageType.SUCCESS.value:
            self._handle_success(data, time_str)
        elif msg_type == MessageType.ERROR.value:
            self._handle_error(data, time_str)

    def _handle_flag_response(self, data: dict, time_str: str):
        """Display flags received from server"""
        flags = data.get('flags', [])
        if not flags:
            display = f"{colorize('No flags found yet.', Colors.GRAY)}"
            self._display_message(display)
            return

        display = f"\n{colorize('🚩 Captured Flags:', Colors.BOLD + Colors.YELLOW)}"
        self._display_message(display)
        
        for idx, flag_info in enumerate(flags, 1):
            flag_timestamp = flag_info.get('timestamp', time.time())
            time_str = format_timestamp(flag_timestamp)
            
            display = f"  {idx}. {colorize(flag_info['content'], Colors.HIGHLIGHT + Colors.GREEN)}"
            self._display_message(display)
            
            display = f"     Found by: {colorize(flag_info['finder'], Colors.GREEN)} in #{colorize(flag_info['room'], Colors.BLUE)}"
            self._display_message(display)
            
            display = f"     Time: {colorize(time_str, Colors.GRAY)}"
            self._display_message(display)
            
            display = f"     Context: {flag_info['message_preview'][:60]}..."
            self._display_message(display)
            
            self._display_message("")  # Empty line for spacing

    def _handle_room_message(self, data: dict, time_str: str):
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
                    username
                )
                
                flag_submit_msg = create_message(MessageType.FLAG_SUBMIT, {
                    'content': flag,
                    'finder': username,
                    'room': room,
                    'message_preview': content[:50]
                })
                self.connection_manager.send_data(flag_submit_msg)

        if username == self.username:
            return

        highlighted_content = self._highlight_flags(content)
        display = f"\n{colorize(f'[{time_str}]', Colors.GRAY)} {colorize(f'{username}', Colors.CYAN)} in {colorize(f'#{room}', Colors.BLUE)}: {highlighted_content}"
        self._display_message(display)

    def _handle_private_message(self, data: dict, time_str: str):
        from_user = data.get("from", "Unknown")
        content = data.get("content", "")
        content = EmojiAliases.replace(content)
        highlighted_content = self._highlight_flags(content)
        display = f"\n{colorize(f'📩 [{time_str}] Private from {from_user}:', Colors.PURPLE)} {highlighted_content}"
        self._display_message(display)

    def _handle_notification(self, data: dict, time_str: str):
        message_text = data.get("message", "")
        display = f"\n{colorize(f'📢 [{time_str}]', Colors.YELLOW)} {message_text}"
        self._display_message(display)

    def _handle_success(self, data: dict, time_str: str):
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
                display = f"  {protection} {colorize(room['name'], Colors.CYAN)} {room_type} - {users_info} users"
                self._display_message(display)

        if users:
            display = f"\n{colorize('👥 Users in room:', Colors.BOLD)}"
            self._display_message(display)
            for user in users:
                role_color = Colors.RED if user["role"] == "admin" else Colors.YELLOW if user["is_moderator"] else Colors.WHITE
                role_symbol = "👑" if user["role"] == "admin" else "⭐" if user["is_moderator"] else "👤"
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

    def _handle_error(self, data: dict, time_str: str):
        message_text = data.get("message", "")
        display = f"\n{colorize('❌ Error:', Colors.RED)} {message_text}"
        self._display_message(display)


class ChatClient:
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.room_manager = RoomManager(self.connection_manager)
        self.flag_detector = FlagDetector()
        self.notification_manager = NotificationManager()
        self.message_handler = MessageHandler(self.flag_detector, self.connection_manager, self.notification_manager)
        self.message_buffer = MessageBuffer()
        self.shell = None
        self.receive_thread = None

    @property
    def connected(self) -> bool:
        return self.connection_manager.connected

    @property
    def username(self) -> str:
        return self.connection_manager.username

    @property
    def current_room(self) -> str:
        return self.room_manager.current_room

    def connect(self, host: str = 'localhost', port: int = 12345, username: str = '') -> bool:
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

    def disconnect(self):
        if self.connected:
            try:
                disconnect_msg = create_message(MessageType.DISCONNECT, {})
                self.connection_manager.send_data(disconnect_msg)
            except:
                pass
            self.connection_manager.disconnect()
            print(f"{colorize('👋 Disconnected from server', Colors.YELLOW)}")

    def send_message(self, content: str) -> bool:
        if not self.connected:
            return False
        message = create_message(MessageType.MESSAGE, {"content": content})
        return self.connection_manager.send_data(message)

    def send_private_message(self, target_user: str, content: str) -> bool:
        if not self.connected:
            return False
        message = create_message(MessageType.PRIVATE_MESSAGE, {
            "target": target_user,
            "content": content
        })
        return self.connection_manager.send_data(message)

    def kick_user(self, username: str) -> bool:
        if not self.connected:
            return False
        message = create_message(MessageType.KICK_USER, {"username": username})
        return self.connection_manager.send_data(message)

    def ban_user(self, username: str) -> bool:
        if not self.connected:
            return False
        message = create_message(MessageType.BAN_USER, {"username": username})
        return self.connection_manager.send_data(message)

    def _receive_loop(self):
        while self.connected:
            data = self.connection_manager.receive_data()
            if data is None:
                break

            self.message_buffer.add_data(data)
            while True:
                message, has_message = self.message_buffer.get_message()
                if not has_message:
                    break
                self.message_handler.handle(message, self.current_room)
                if self.shell:
                    self.shell.show_prompt()

        self.connection_manager.disconnect()
        if self.shell:
            print(f"\n{colorize('Connection lost. Type connect to reconnect.', Colors.RED)}")

    def display_flags(self):
        message = create_message(MessageType.FLAG_REQUEST, {})
        self.connection_manager.send_data(message)

class ModerationCommands:
    def __init__(self, client: ChatClient):
        self.client = client

    def kick(self, username: str) -> bool:
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        return self.client.kick_user(username)

    def ban(self, username: str) -> bool:
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return False
        return self.client.ban_user(username)


class ChatShell(cmd.Cmd):
    def __init__(self, client: ChatClient):
        super().__init__()
        self.client = client
        self.moderation = ModerationCommands(client)
        self.setup_message_display()
        self.update_prompt()

    def setup_message_display(self):
        def display_callback(text: str):
            print(text)

        self.client.message_handler.subscribe(display_callback)

    def update_prompt(self):
        if self.client.connected and self.client.username:
            room_info = f"#{self.client.current_room}" if self.client.current_room else "#no-room"
            self.prompt = f"{colorize(self.client.username, Colors.CYAN)}{colorize(room_info, Colors.BLUE)} > "
        else:
            self.prompt = f"{colorize('Not connected', Colors.RED)} > "

    def show_prompt(self):
        self.update_prompt()
        if hasattr(self, 'stdout'):
            self.stdout.write(self.prompt)
            self.stdout.flush()

    def emptyline(self):
        pass

    def default(self, line):
        if not self.client.connected:
            print(f"{colorize('❌ Not connected. Use connect command first.', Colors.RED)}")
            return
        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room. Use join command first.', Colors.RED)}")
            return
        if line.strip():
            self.client.send_message(line.strip())

    def do_help(self, arg):
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
        print(f"  {colorize('emojis', Colors.CYAN)} - Display all emoji aliases\"")

        print(f"\n{colorize('Moderation Commands:', Colors.YELLOW)}")
        print(f"  {colorize('kick <username>', Colors.CYAN)} - Kick user from room (moderators only)")
        print(f"  {colorize('ban <username>', Colors.CYAN)} - Ban user from room (moderators only)")

        print(f"\n{colorize('Other Commands:', Colors.YELLOW)}")
        print(f"  {colorize('status', Colors.CYAN)} - Show connection status")
        print(f"  {colorize('clear', Colors.CYAN)} - Clear screen")
        print(f"  {colorize('help', Colors.CYAN)} - Show this help\n")

    def do_connect(self, args):
        if self.client.connected:
            print(f"{colorize('❌ Already connected. Disconnect first.', Colors.RED)}")
            return

        parts = args.split()
        host = parts[0] if parts else input(f"{colorize('Enter server host (localhost):', Colors.CYAN)} ").strip() or 'localhost'

        try:
            port = int(parts[1]) if len(parts) > 1 else int(input(f"{colorize('Enter server port (12345):', Colors.CYAN)} ").strip() or '12345')
        except ValueError:
            print(f"{colorize('❌ Invalid port number', Colors.RED)}")
            return

        username = parts[2] if len(parts) > 2 else input(f"{colorize('Enter username:', Colors.CYAN)} ").strip()

        if not username:
            print(f"{colorize('❌ Username is required', Colors.RED)}")
            return

        print(f"{colorize('🔄 Connecting to', Colors.YELLOW)} {host}:{port} {colorize('as', Colors.YELLOW)} {username}...")

        if self.client.connect(host, port, username):
            print(f"{colorize('✅ Connected successfully!', Colors.GREEN)}")
            self.update_prompt()
        else:
            print(f"{colorize('❌ Connection failed', Colors.RED)}")

    def do_disconnect(self, args):
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        self.client.disconnect()
        self.update_prompt()

    def do_join(self, args):
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

    def do_leave(self, args):
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room', Colors.RED)}")
            return
        if self.client.room_manager.leave():
            self.update_prompt()

    def do_create(self, args):
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

    def do_rooms(self, args):
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        self.client.room_manager.list_rooms()

    def do_users(self, args):
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room', Colors.RED)}")
            return
        self.client.room_manager.list_users()

    def do_msg(self, args):
        self._send_private_message(args)

    def do_pm(self, args):
        self._send_private_message(args)

    def do_emojis(self, args):
        print(f"\n{colorize('😊 Emoji Aliases', Colors.BOLD + Colors.YELLOW)}")
        print(f"{colorize('Use these secret phrases to add emojis to your messages:', Colors.GRAY)}\n")
        print(EmojiAliases.list_aliases())
        print(f"\n{colorize('Example:', Colors.YELLOW)} I love this :heart: :fire: :rocket:\n")


    def _send_private_message(self, args):
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

    def do_kick(self, args):
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not args.strip():
            print(f"{colorize('❌ Usage: kick <username>', Colors.RED)}")
            return
        self.moderation.kick(args.strip())

    def do_ban(self, args):
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return
        if not args.strip():
            print(f"{colorize('❌ Usage: ban <username>', Colors.RED)}")
            return
        self.moderation.ban(args.strip())

    def do_flags(self, args):
        self.client.display_flags()

    def do_flag_count(self, args):
        count = len(self.client.flag_detector.get_all_flags())
        print(f"{colorize(f'🚩 Total flags captured: {count}', Colors.BOLD + Colors.YELLOW)}")

    def do_status(self, args):
        if self.client.connected:
            print(f"{colorize('✅ Connected as:', Colors.GREEN)} {self.client.username}")
            print(f"{colorize('🏠 Current room:', Colors.CYAN)} {self.client.current_room or 'None'}")
        else:
            print(f"{colorize('❌ Not connected', Colors.RED)}")

    def do_clear(self, args):
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_quit(self, args):
        return self.do_exit(args)

    def do_exit(self, args):
        if self.client.connected:
            self.client.disconnect()
        print(f"{colorize('👋 Goodbye!', Colors.GREEN)}")
        return True


def show_banner():
    banner = f"""
{colorize('╔══════════════════════════════════════════════════════════╗', Colors.CYAN)}
{colorize('║', Colors.CYAN)} {colorize('🚀 Drevoid LAN Chat Client', Colors.BOLD + Colors.WHITE)} {' ' * 23} {colorize('║', Colors.CYAN)}
{colorize('║', Colors.CYAN)} {colorize('Terminal-based chat with rooms & private messaging', Colors.WHITE)} {' ' * 7} {colorize('║', Colors.CYAN)}
{colorize('╚══════════════════════════════════════════════════════════╝', Colors.CYAN)}

{colorize('💡 Quick Start:', Colors.YELLOW)}
  1. Type '{colorize('connect', Colors.CYAN)}' to connect to a server
  2. Type '{colorize('help', Colors.CYAN)}' for all available commands
  3. Start chatting in rooms or send private messages!

{colorize('🎯 Pro Tips:', Colors.YELLOW)}
  • Use '{colorize('join general', Colors.CYAN)}' to join the default room
  • Use '{colorize('msg username message', Colors.CYAN)}' for private messages
  • Use '{colorize('create myroom private password123', Colors.CYAN)}' for private rooms
  • Use '{colorize('flags', Colors.CYAN)}' to view all captured CTF flags
"""
    print(banner)


def main():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        show_banner()

        client = ChatClient()
        shell = ChatShell(client)
        client.shell = shell

        if len(sys.argv) >= 4:
            host = sys.argv[1]
            try:
                port = int(sys.argv[2])
                username = sys.argv[3]

                print(f"{colorize('🔄 Auto-connecting...', Colors.YELLOW)}")
                if client.connect(host, port, username):
                    print(f"{colorize('✅ Connected successfully!', Colors.GREEN)}")
                    shell.update_prompt()
                else:
                    print(f"{colorize('❌ Auto-connect failed', Colors.RED)}")
            except ValueError:
                print(f"{colorize('❌ Invalid port in arguments', Colors.RED)}")

        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print(f"\n{colorize('👋 Interrupted by user', Colors.YELLOW)}")

    except Exception as e:
        print(f"{colorize('❌ Application error:', Colors.RED)} {e}")

    finally:
        if 'client' in locals() and client.connected:
            client.disconnect()