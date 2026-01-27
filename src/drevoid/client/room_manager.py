"""Room management operations."""

from typing import Optional
from ..core.protocol import MessageType, create_message


class RoomManager:
    """Manages room-related operations."""

    def __init__(self, connection_manager: "ConnectionManager"):
        """
        Initialize room manager.

        Args:
            connection_manager: Connection manager instance
        """
        self.connection_manager = connection_manager
        self.current_room: Optional[str] = None

    def join(self, room_name: str, password: str = "") -> bool:
        """
        Join a room.

        Args:
            room_name: Name of room to join
            password: Password if private room

        Returns:
            True if successful
        """
        message = create_message(
            MessageType.JOIN_ROOM,
            {"room_name": room_name, "password": password},
        )
        if self.connection_manager.send_data(message):
            self.current_room = room_name
            return True
        return False

    def leave(self) -> bool:
        """
        Leave current room.

        Returns:
            True if successful
        """
        if not self.current_room:
            return False
        message = create_message(MessageType.LEAVE_ROOM, {})
        if self.connection_manager.send_data(message):
            self.current_room = None
            return True
        return False

    def create(self, room_name: str, room_type: str = "public", password: str = "") -> bool:
        """
        Create a new room.

        Args:
            room_name: Name for new room
            room_type: Type (public or private)
            password: Password for private rooms

        Returns:
            True if successful
        """
        message = create_message(
            MessageType.CREATE_ROOM,
            {
                "room_name": room_name,
                "room_type": room_type,
                "password": password,
            },
        )
        return self.connection_manager.send_data(message)

    def list_rooms(self) -> bool:
        """
        Request list of available rooms.

        Returns:
            True if request sent successfully
        """
        message = create_message(MessageType.LIST_ROOMS, {})
        return self.connection_manager.send_data(message)

    def list_users(self) -> bool:
        """
        Request list of users in current room.

        Returns:
            True if request sent successfully
        """
        message = create_message(MessageType.LIST_USERS, {})
        return self.connection_manager.send_data(message)
