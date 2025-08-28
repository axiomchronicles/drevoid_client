"""
Drevoid LAN Chat Client with Interactive Shell
Features: Room management, private messaging, Drevoid commands
"""

import socket
import threading
import cmd
import json
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from script.protocol import *

class ChatClient:
    """Main chat client class"""
    def __init__(self):
        self.socket = None
        self.connected = False
        self.username = None
        self.current_room = None
        self.buffer = b''
        self.shell = None

    def connect(self, host='localhost', port=12345, username=''):
        """Connect to chat server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True

            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()

            if username:
                self.username = username
                connect_msg = create_message(MessageType.CONNECT, {"username": username})
                self.send_message(connect_msg)

            return True

        except Exception as e:
            print(f"{colorize('❌ Connection failed:', Colors.RED)} {e}")
            return False

    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            self.connected = False
            if self.socket:
                try:
                    disconnect_msg = create_message(MessageType.DISCONNECT, {})
                    self.send_message(disconnect_msg)
                    self.socket.close()
                except:
                    pass
            print(f"{colorize('👋 Disconnected from server', Colors.YELLOW)}")

    def send_message(self, message: dict):
        """Send message to server"""
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

    def receive_messages(self):
        """Receive messages from server"""
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break

                self.buffer += data
                while True:
                    message, self.buffer = deserialize_message(self.buffer)
                    if message is None:
                        break
                    self.handle_message(message)

            except Exception as e:
                if self.connected:
                    print(f"{colorize('❌ Receive error:', Colors.RED)} {e}")
                break

        self.connected = False
        if self.shell:
            print(f"\n{colorize('Connection lost. Type \'connect\' to reconnect.', Colors.RED)}")

    def handle_message(self, message: dict):
        """Handle incoming messages"""
        msg_type = message.get("type")
        data = message.get("data", {})
        timestamp = message.get("timestamp", time.time())
        time_str = format_timestamp(timestamp)

        if msg_type == MessageType.MESSAGE.value:
            username = data.get("username", "Unknown")
            content = data.get("content", "")
            room = data.get("room", "")

            if username == self.username:
                return  

            print(f"\n{colorize(f'[{time_str}]', Colors.GRAY)} {colorize(f'{username}', Colors.CYAN)} in {colorize(f'#{room}', Colors.BLUE)}: {content}")

        elif msg_type == MessageType.PRIVATE_MESSAGE.value:
            from_user = data.get("from", "Unknown")
            content = data.get("content", "")
            print(f"\n{colorize(f'📩 [{time_str}] Private from {from_user}:', Colors.PURPLE)} {content}")

        elif msg_type == MessageType.NOTIFICATION.value:
            message_text = data.get("message", "")
            print(f"\n{colorize(f'📢 [{time_str}]', Colors.YELLOW)} {message_text}")

        elif msg_type == MessageType.SUCCESS.value:
            message_text = data.get("message", "")
            rooms = data.get("rooms", [])
            users = data.get("users", [])
            stats = data.get("stats", {})

            print(f"\n{colorize('✅', Colors.GREEN)} {message_text}")

            if rooms:
                print(f"\n{colorize('🏠 Available Rooms:', Colors.BOLD)}")
                for room in rooms:
                    protection = "🔒" if room["password_protected"] else "🔓"
                    room_type = f"({room['type']})"
                    users_info = f"{room['users']}/{room['max_users']}"
                    print(f"  {protection} {colorize(room['name'], Colors.CYAN)} {room_type} - {users_info} users")

            if users:
                print(f"\n{colorize('👥 Users in room:', Colors.BOLD)}")
                for user in users:
                    role_color = Colors.RED if user["role"] == "admin" else Colors.YELLOW if user["is_moderator"] else Colors.WHITE
                    role_symbol = "👑" if user["role"] == "admin" else "⭐" if user["is_moderator"] else "👤"
                    print(f"  {role_symbol} {colorize(user['username'], role_color)}")

            if stats:
                uptime = stats.get("uptime", 0)
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                print(f"\n{colorize('📊 Server Stats:', Colors.BOLD)}")
                print(f"  Users: {stats.get('connected_users', 0)}")
                print(f"  Rooms: {stats.get('active_rooms', 0)}")
                print(f"  Uptime: {hours:02d}:{minutes:02d}")

        elif msg_type == MessageType.ERROR.value:
            message_text = data.get("message", "")
            print(f"\n{colorize('❌ Error:', Colors.RED)} {message_text}")

        if self.shell:
            self.shell.show_prompt()

class ChatShell(cmd.Cmd):
    """Interactive command shell for chat client"""

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.update_prompt()

    def update_prompt(self):
        """Update command prompt"""
        if self.client.connected and self.client.username:
            room_info = f"#{self.client.current_room}" if self.client.current_room else "#no-room"
            self.prompt = f"{colorize(self.client.username, Colors.CYAN)}{colorize(room_info, Colors.BLUE)} > "
        else:
            self.prompt = f"{colorize('Not connected', Colors.RED)} > "

    def show_prompt(self):
        """Show the prompt (used after receiving messages)"""
        self.update_prompt()
        if hasattr(self, 'stdout'):
            self.stdout.write(self.prompt)
            self.stdout.flush()

    def emptyline(self):
        """Do nothing on empty line"""
        pass

    def default(self, line):
        """Handle regular chat messages"""
        if self.client.connected and self.client.current_room and line.strip():
            message = create_message(MessageType.MESSAGE, {"content": line.strip()})
            self.client.send_message(message)
        elif not self.client.connected:
            print(f"{colorize('❌ Not connected. Use \'connect\' command first.', Colors.RED)}")
        elif not self.client.current_room:
            print(f"{colorize('❌ Not in any room. Use \'join\' command first.', Colors.RED)}")

    def do_help(self, arg):
        """Show help information"""
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

        print(f"\n{colorize('Moderation Commands:', Colors.YELLOW)}")
        print(f"  {colorize('kick <username>', Colors.CYAN)} - Kick user from room (moderators only)")
        print(f"  {colorize('ban <username>', Colors.CYAN)} - Ban user from room (moderators only)")

        print(f"\n{colorize('Other Commands:', Colors.YELLOW)}")
        print(f"  {colorize('status', Colors.CYAN)} - Show connection status")
        print(f"  {colorize('clear', Colors.CYAN)} - Clear screen")
        print(f"  {colorize('help', Colors.CYAN)} - Show this help\n")

    def do_connect(self, args):
        """Connect to server: connect [host] [port] [username]"""
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
        """Disconnect from server"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        self.client.disconnect()
        self.update_prompt()

    def do_join(self, args):
        """Join a room: join <room_name> [password]"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        parts = args.split(None, 1)
        if not parts:
            print(f"{colorize('❌ Usage: join <room_name> [password]', Colors.RED)}")
            return

        room_name = parts[0]
        password = parts[1] if len(parts) > 1 else ""

        message = create_message(MessageType.JOIN_ROOM, {
            "room_name": room_name,
            "password": password
        })

        if self.client.send_message(message):
            self.client.current_room = room_name
            self.update_prompt()

    def do_leave(self, args):
        """Leave current room"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room', Colors.RED)}")
            return

        message = create_message(MessageType.LEAVE_ROOM, {})
        if self.client.send_message(message):
            self.client.current_room = None
            self.update_prompt()

    def do_create(self, args):
        """Create a room: create <room_name> [private] [password]"""
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

        message = create_message(MessageType.CREATE_ROOM, {
            "room_name": room_name,
            "room_type": room_type,
            "password": password
        })

        self.client.send_message(message)

    def do_rooms(self, args):
        """List available rooms"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        message = create_message(MessageType.LIST_ROOMS, {})
        self.client.send_message(message)

    def do_users(self, args):
        """List users in current room"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        if not self.client.current_room:
            print(f"{colorize('❌ Not in any room', Colors.RED)}")
            return

        message = create_message(MessageType.LIST_USERS, {})
        self.client.send_message(message)

    def do_msg(self, args):
        """Send private message: msg <username> <message>"""
        self._send_private_message(args)

    def do_pm(self, args):
        """Send private message: pm <username> <message>"""
        self._send_private_message(args)

    def _send_private_message(self, args):
        """Helper method for private messages"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        parts = args.split(None, 1)
        if len(parts) < 2:
            print(f"{colorize('❌ Usage: msg <username> <message>', Colors.RED)}")
            return

        target_user = parts[0]
        content = parts[1]

        message = create_message(MessageType.PRIVATE_MESSAGE, {
            "target": target_user,
            "content": content
        })

        self.client.send_message(message)

    def do_kick(self, args):
        """Kick user from room: kick <username>"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        if not args.strip():
            print(f"{colorize('❌ Usage: kick <username>', Colors.RED)}")
            return

        message = create_message(MessageType.KICK_USER, {"username": args.strip()})
        self.client.send_message(message)

    def do_ban(self, args):
        """Ban user from room: ban <username>"""
        if not self.client.connected:
            print(f"{colorize('❌ Not connected', Colors.RED)}")
            return

        if not args.strip():
            print(f"{colorize('❌ Usage: ban <username>', Colors.RED)}")
            return

        message = create_message(MessageType.BAN_USER, {"username": args.strip()})
        self.client.send_message(message)

    def do_status(self, args):
        """Show connection status"""
        if self.client.connected:
            print(f"{colorize('✅ Connected as:', Colors.GREEN)} {self.client.username}")
            print(f"{colorize('🏠 Current room:', Colors.CYAN)} {self.client.current_room or 'None'}")
        else:
            print(f"{colorize('❌ Not connected', Colors.RED)}")

    def do_clear(self, args):
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def do_quit(self, args):
        """Exit the application"""
        return self.do_exit(args)

    def do_exit(self, args):
        """Exit the application"""
        if self.client.connected:
            self.client.disconnect()

        print(f"{colorize('👋 Goodbye!', Colors.GREEN)}")
        return True

def show_banner():
    """Show application banner"""
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
"""
    print(banner)

def main():
    """Main client function"""
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

if __name__ == "__main__":
    main()
