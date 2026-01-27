"""Server-side room management."""

from typing import Set, Dict
from ..core.protocol import RoomType, hash_password, ThreadSafeDict


class ServerRoomManager:
    """Manages room state and operations on server."""

    def __init__(self):
        """Initialize room manager."""
        self.rooms = ThreadSafeDict()
        self.user_rooms = ThreadSafeDict()
        self.room_histories: Dict[str, list] = {}
        self.banned_users: Dict[str, Set[str]] = {}
        self.muted_users: Dict[str, Set[str]] = {}

        # Create default general room
        self.create_room("general", RoomType.PUBLIC, "")

    def create_room(
        self, room_name: str, room_type: RoomType, password: str, max_users: int = 50
    ) -> bool:
        """
        Create a new room.

        Args:
            room_name: Name of room
            room_type: Type (public/private)
            password: Password for private rooms
            max_users: Maximum concurrent users

        Returns:
            True if created, False if already exists
        """
        if room_name in self.rooms.keys():
            return False

        pwd_hash = hash_password(password) if room_type == RoomType.PRIVATE else ""

        self.rooms[room_name] = {
            "type": room_type.value,
            "password_hash": pwd_hash,
            "users": set(),
            "max_users": max_users,
            "password_protected": bool(password),
        }
        self.room_histories[room_name] = []
        self.banned_users[room_name] = set()
        self.muted_users[room_name] = set()
        return True

    def delete_room(self, room_name: str) -> bool:
        """Delete a room."""
        if room_name not in self.rooms.keys() or room_name == "general":
            return False
        del self.rooms[room_name]
        self.room_histories.pop(room_name, None)
        self.banned_users.pop(room_name, None)
        self.muted_users.pop(room_name, None)
        return True

    def add_user_to_room(self, username: str, room_name: str) -> bool:
        """Add user to room."""
        if room_name not in self.rooms.keys():
            return False
        self.rooms[room_name]["users"].add(username)
        self.user_rooms[username] = room_name
        return True

    def remove_user_from_room(self, username: str, room_name: str) -> bool:
        """Remove user from room."""
        if room_name not in self.rooms.keys():
            return False
        self.rooms[room_name]["users"].discard(username)
        if username in self.user_rooms.keys():
            self.user_rooms.pop(username)
        return True

    def get_room_users(self, room_name: str) -> Set[str]:
        """Get users in room."""
        if room_name not in self.rooms.keys():
            return set()
        return self.rooms[room_name]["users"].copy()

    def get_user_room(self, username: str) -> str | None:
        """Get room user is in."""
        return self.user_rooms.get(username)

    def is_user_banned(self, username: str, room_name: str) -> bool:
        """Check if user is banned from room."""
        return username in self.banned_users.get(room_name, set())

    def is_user_muted(self, username: str, room_name: str) -> bool:
        """Check if user is muted in room."""
        return username in self.muted_users.get(room_name, set())

    def ban_user(self, username: str, room_name: str) -> bool:
        """Ban user from room."""
        if room_name not in self.banned_users:
            self.banned_users[room_name] = set()
        self.banned_users[room_name].add(username)
        return True

    def mute_user(self, username: str, room_name: str) -> bool:
        """Mute user in room."""
        if room_name not in self.muted_users:
            self.muted_users[room_name] = set()
        self.muted_users[room_name].add(username)
        return True

    def unmute_user(self, username: str, room_name: str) -> bool:
        """Unmute user in room."""
        if room_name not in self.muted_users:
            return False
        self.muted_users[room_name].discard(username)
        return True

    def log_room_event(self, room_name: str, event: str) -> None:
        """Log event to room history."""
        if room_name in self.room_histories:
            self.room_histories[room_name].append(event)

    def get_room_history(self, room_name: str) -> list:
        """Get room event history."""
        return self.room_histories.get(room_name, []).copy()
