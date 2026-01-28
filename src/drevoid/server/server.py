"""Main chat server implementation."""

import socket
import threading
import time
import argparse
from typing import Optional

from ..core.protocol import (
    MessageType,
    UserRole,
    RoomType,
    serialize_message,
    deserialize_message,
    create_message,
    hash_password,
)
from ..common.logging import Logger
from .room_manager import ServerRoomManager
from .client_handler import ClientHandler
from .admin_console import AdminConsole


class ChatServer:
    """
    Multi-threaded chat server.

    Manages client connections, rooms, messaging, and flag storage.
    """

    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORT = 8891

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, enable_logging: bool = True):
        """
        Initialize chat server.

        Args:
            host: Bind host
            port: Bind port
            enable_logging: Enable logging output
        """
        self.host = host
        self.port = port
        self.logger = Logger(enable_timestamps=enable_logging)

        self.socket: Optional[socket.socket] = None
        self.running = False
        self.start_time = time.time()

        self.room_manager = ServerRoomManager()
        self.client_handler = ClientHandler(self.logger)

        self.history_logs = []

    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        entry = f"[{level.upper()}] {message}"
        self.history_logs.append(entry)

        if level == "info":
            self.logger.info(message)
        elif level == "success":
            self.logger.success(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)

    def start(self) -> None:
        """Start the server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(100)
            self.running = True
            self.start_time = time.time()

            self.log(f"Server starting on {self.host}:{self.port}", "success")

            # Start admin console in background
            threading.Thread(target=self._admin_console, daemon=True).start()

            # Accept connections
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, addr),
                        daemon=True,
                    )
                    thread.start()
                except KeyboardInterrupt:
                    self.stop()
                except Exception as e:
                    self.log(f"Accept error: {e}", "error")

        except Exception as e:
            self.log(f"Server error: {e}", "error")
        finally:
            self._cleanup()

    def stop(self) -> None:
        """Stop the server."""
        self.running = False
        self.log("Server shutting down", "warning")

    def _cleanup(self) -> None:
        """Clean up server resources."""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass

    def _handle_client(self, client_socket: socket.socket, addr) -> None:
        """
        Handle individual client connection (runs in thread).

        Args:
            client_socket: Client socket
            addr: Client address
        """
        username = None
        buffer = b""

        try:
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break

                buffer += chunk

                while True:
                    message, buffer = deserialize_message(buffer)
                    if message is None:
                        break

                    msg_type = message.get("type")
                    data = message.get("data", {})

                    # Track username for successful CONNECT
                    if msg_type == MessageType.CONNECT.value and username is None:
                        username = data.get("username", "").strip()
                    
                    if not self._process_message(client_socket, addr, username, msg_type, data):
                        break

        except Exception as e:
            self.log(f"Client error: {e}", "error")
        finally:
            # Cleanup on disconnect
            if username and username in self.client_handler.clients.keys():
                self._handle_disconnect(username)

            try:
                client_socket.close()
            except Exception:
                pass

    def _process_message(self, client_socket: socket.socket, addr, username: Optional[str], msg_type: str, data: dict) -> bool:
        """
        Process incoming message.

        Args:
            client_socket: Client socket
            addr: Client address
            username: Connected username (or None if not connected)
            msg_type: Message type
            data: Message data

        Returns:
            True to continue connection
        """
        # CONNECT
        if msg_type == MessageType.CONNECT.value:
            return self._handle_connect(client_socket, addr, data)

        # Must be authenticated
        if not username or username not in self.client_handler.clients.keys():
            self._send_to_socket(client_socket, MessageType.ERROR, {"message": "Not authenticated"})
            return False

        # Route to handler based on type
        if msg_type == MessageType.DISCONNECT.value:
            return False
        elif msg_type == MessageType.CREATE_ROOM.value:
            self._handle_create_room(username, data)
        elif msg_type == MessageType.LIST_ROOMS.value:
            self._handle_list_rooms(username)
        elif msg_type == MessageType.JOIN_ROOM.value:
            self._handle_join_room(username, data)
        elif msg_type == MessageType.LEAVE_ROOM.value:
            self._handle_leave_room(username)
        elif msg_type == MessageType.LIST_USERS.value:
            self._handle_list_users(username)
        elif msg_type == MessageType.MESSAGE.value:
            self._handle_room_message(username, data)
        elif msg_type == MessageType.PRIVATE_MESSAGE.value:
            self._handle_private_message(username, data)
        elif msg_type == MessageType.KICK_USER.value:
            self._handle_kick_user(username, data)
        elif msg_type == MessageType.BAN_USER.value:
            self._handle_ban_user(username, data)
        elif msg_type == MessageType.FLAG_SUBMIT.value:
            self._handle_flag_submit(username, data)
        elif msg_type == MessageType.FLAG_REQUEST.value:
            self._handle_flag_request(username)

        return True

    def _send_to_socket(self, sock: socket.socket, msg_type: MessageType, data: dict) -> None:
        """Send message to socket."""
        try:
            message = create_message(msg_type, data)
            sock.send(serialize_message(message))
        except Exception:
            pass

    def _handle_connect(self, client_socket: socket.socket, addr, data: dict) -> bool:
        """Handle client connect."""
        username = data.get("username", "").strip()

        if not username or username in self.client_handler.clients.keys():
            self._send_to_socket(client_socket, MessageType.ERROR, {"message": "Username invalid or taken"})
            return False

        if not self.client_handler.register_client(username, client_socket, addr, UserRole.USER.value):
            self._send_to_socket(client_socket, MessageType.ERROR, {"message": "Connection failed"})
            return False

        self._send_to_socket(client_socket, MessageType.SUCCESS, {"message": "Connected"})
        self._send_server_status(username)
        self.log(f"User connected: {username}", "success")
        return True

    def _handle_create_room(self, username: str, data: dict) -> None:
        """Handle room creation."""
        room_name = data.get("room_name", "").strip()
        room_type = data.get("room_type", "public")
        password = data.get("password", "")

        if not room_name or room_name in self.room_manager.rooms.keys():
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Room invalid or exists"})
            return

        room_type_enum = RoomType.PRIVATE if room_type == "private" else RoomType.PUBLIC
        if self.room_manager.create_room(room_name, room_type_enum, password):
            self.client_handler.send_to_client(username, MessageType.SUCCESS, {"message": f"Room {room_name} created"})
            self.log(f"Room created: {room_name} by {username}", "info")

    def _handle_list_rooms(self, username: str) -> None:
        """Handle room list request."""
        room_list = []
        for room_name in self.room_manager.rooms.keys():
            room_info = self.room_manager.rooms[room_name]
            room_list.append({
                "name": room_name,
                "type": room_info["type"],
                "password_protected": room_info["password_protected"],
                "users": len(room_info["users"]),
                "max_users": room_info["max_users"],
            })

        self.client_handler.send_to_client(
            username,
            MessageType.SUCCESS,
            {
                "message": "Room list",
                "rooms": room_list,
                "stats": self._get_server_stats(),
            },
        )

    def _handle_join_room(self, username: str, data: dict) -> None:
        """Handle room join."""
        room_name = data.get("room_name", "").strip()
        password = data.get("password", "")

        if room_name not in self.room_manager.rooms.keys():
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Room not found"})
            return

        if self.room_manager.is_user_banned(username, room_name):
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "You are banned"})
            return

        room_info = self.room_manager.rooms[room_name]

        if room_info["type"] == "private" and hash_password(password) != room_info["password_hash"]:
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Invalid password"})
            return

        if len(room_info["users"]) >= room_info["max_users"]:
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Room full"})
            return

        # Leave previous room
        old_room = self.room_manager.get_user_room(username)
        if old_room:
            self.room_manager.remove_user_from_room(username, old_room)
            self.client_handler.broadcast_to_room(
                self.room_manager,
                old_room,
                MessageType.NOTIFICATION,
                {"message": f"{username} left"},
                exclude=username,
            )
            self.room_manager.log_room_event(old_room, f"{username} left")

        # Join new room
        self.room_manager.add_user_to_room(username, room_name)
        self.client_handler.send_to_client(username, MessageType.SUCCESS, {"message": f"Joined {room_name}"})
        self.client_handler.broadcast_to_room(
            self.room_manager,
            room_name,
            MessageType.NOTIFICATION,
            {"message": f"{username} joined"},
            exclude=username,
        )
        self.room_manager.log_room_event(room_name, f"{username} joined")
        self.log(f"{username} joined room {room_name}", "info")

    def _handle_leave_room(self, username: str) -> None:
        """Handle room leave."""
        room_name = self.room_manager.get_user_room(username)

        if not room_name:
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Not in a room"})
            return

        self.room_manager.remove_user_from_room(username, room_name)
        self.client_handler.send_to_client(username, MessageType.SUCCESS, {"message": f"Left {room_name}"})
        self.client_handler.broadcast_to_room(
            self.room_manager,
            room_name,
            MessageType.NOTIFICATION,
            {"message": f"{username} left"},
        )
        self.room_manager.log_room_event(room_name, f"{username} left")
        self.log(f"{username} left room {room_name}", "info")

    def _handle_list_users(self, username: str) -> None:
        """Handle user list request."""
        room_name = self.room_manager.get_user_room(username)

        if not room_name:
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Not in a room"})
            return

        user_list = []
        for user in self.room_manager.get_room_users(room_name):
            role = self.client_handler.get_client_role(user) or "user"
            user_list.append({
                "username": user,
                "role": role,
                "is_moderator": role in ("moderator", "admin"),
            })

        self.client_handler.send_to_client(
            username,
            MessageType.SUCCESS,
            {"message": f"Users in {room_name}", "users": user_list},
        )

    def _handle_room_message(self, username: str, data: dict) -> None:
        """Handle room message."""
        room_name = self.room_manager.get_user_room(username)
        content = data.get("content", "")

        if not room_name:
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Not in a room"})
            return

        self.client_handler.broadcast_to_room(
            self.room_manager,
            room_name,
            MessageType.MESSAGE,
            {
                "username": username,
                "content": content,
                "room": room_name,
            },
            exclude=username,
        )
        self.room_manager.log_room_event(room_name, f"{username}: {content[:30]}")

    def _handle_private_message(self, username: str, data: dict) -> None:
        """Handle private message."""
        target = data.get("target", "")
        content = data.get("content", "")

        if target not in self.client_handler.clients.keys():
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "User not found"})
            return

        self.client_handler.send_to_client(target, MessageType.PRIVATE_MESSAGE, {
            "from": username,
            "content": content,
        })
        self.client_handler.send_to_client(username, MessageType.SUCCESS, {"message": f"Message sent to {target}"})

    def _handle_kick_user(self, username: str, data: dict) -> None:
        """Handle user kick."""
        role = self.client_handler.get_client_role(username)
        if role not in ("moderator", "admin"):
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Permission denied"})
            return

        target = data.get("username", "")
        room_name = self.room_manager.get_user_room(username)

        if not room_name or target not in self.room_manager.get_room_users(room_name):
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "User not in room"})
            return

        self.room_manager.remove_user_from_room(target, room_name)
        self.client_handler.send_to_client(target, MessageType.NOTIFICATION, {"message": f"You were kicked from {room_name}"})
        self.client_handler.broadcast_to_room(
            self.room_manager,
            room_name,
            MessageType.NOTIFICATION,
            {"message": f"{target} was kicked by {username}"},
        )
        self.log(f"{target} kicked from {room_name} by {username}", "warn")

    def _handle_ban_user(self, username: str, data: dict) -> None:
        """Handle user ban."""
        role = self.client_handler.get_client_role(username)
        if role not in ("moderator", "admin"):
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Permission denied"})
            return

        target = data.get("username", "")
        room_name = self.room_manager.get_user_room(username)

        if not room_name or target not in self.room_manager.get_room_users(room_name):
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "User not in room"})
            return

        self.room_manager.remove_user_from_room(target, room_name)
        self.room_manager.ban_user(target, room_name)
        self.client_handler.send_to_client(target, MessageType.NOTIFICATION, {"message": f"You were banned from {room_name}"})
        self.client_handler.broadcast_to_room(
            self.room_manager,
            room_name,
            MessageType.NOTIFICATION,
            {"message": f"{target} was banned by {username}"},
        )
        self.log(f"{target} banned from {room_name} by {username}", "warning")

    def _handle_flag_submit(self, username: str, data: dict) -> None:
        """Handle flag submission."""
        flag_content = data.get("content", "").strip()
        if not flag_content or not self.client_handler.store_flag(
            flag_content,
            username,
            data.get("room", ""),
            data.get("message_preview", ""),
        ):
            self.client_handler.send_to_client(username, MessageType.ERROR, {"message": "Flag already recorded"})
            return

        self.client_handler.send_to_client(username, MessageType.SUCCESS, {"message": "Flag recorded"})
        self.log(f"Flag captured: {flag_content} by {username}", "success")

    def _handle_flag_request(self, username: str) -> None:
        """Handle flag list request."""
        flags = self.client_handler.get_all_flags()
        self.client_handler.send_to_client(
            username,
            MessageType.FLAG_RESPONSE,
            {"flags": flags, "total": len(flags)},
        )

    def _send_server_status(self, username: str) -> None:
        """Send server status to client."""
        room_list = []
        for room_name in self.room_manager.rooms.keys():
            room_info = self.room_manager.rooms[room_name]
            room_list.append({
                "name": room_name,
                "type": room_info["type"],
                "password_protected": room_info["password_protected"],
                "users": len(room_info["users"]),
                "max_users": room_info["max_users"],
            })

        self.client_handler.send_to_client(
            username,
            MessageType.SUCCESS,
            {
                "message": "Welcome to Drevoid",
                "rooms": room_list,
                "stats": self._get_server_stats(),
            },
        )

    def _get_server_stats(self) -> dict:
        """Get server statistics."""
        uptime = int(time.time() - self.start_time)
        active_rooms = len([r for r in self.room_manager.rooms.keys() if self.room_manager.rooms[r]["users"]])

        return {
            "connected_users": len(self.client_handler.clients.keys()),
            "active_rooms": active_rooms,
            "uptime": uptime,
        }

    def _handle_disconnect(self, username: str) -> None:
        """Handle client disconnect cleanup."""
        room_name = self.room_manager.get_user_room(username)
        if room_name:
            self.room_manager.remove_user_from_room(username, room_name)
            self.client_handler.broadcast_to_room(
                self.room_manager,
                room_name,
                MessageType.NOTIFICATION,
                {"message": f"{username} disconnected"},
            )
            self.room_manager.log_room_event(room_name, f"{username} disconnected")

        self.client_handler.unregister_client(username)
        self.log(f"User disconnected: {username}", "info")

    def _admin_console(self) -> None:
        """Advanced admin console interface (runs in background thread)."""
        console = AdminConsole(self)
        console.cmdloop()


def main():
    """Main entry point for server."""
    parser = argparse.ArgumentParser(description="Start Drevoid chat server")
    parser.add_argument("--host", type=str, default=ChatServer.DEFAULT_HOST, help="Bind host")
    parser.add_argument("--port", type=int, default=ChatServer.DEFAULT_PORT, help="Bind port")
    args = parser.parse_args()

    server = ChatServer(args.host, args.port)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
