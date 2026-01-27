# API Documentation

## Core Protocol (`drevoid.core.protocol`)

### Message Types

```python
class MessageType(Enum):
    # Connection
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    
    # Rooms
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    LIST_ROOMS = "list_rooms"
    
    # Messaging
    MESSAGE = "message"
    PRIVATE_MESSAGE = "private_message"
    
    # User Management
    LIST_USERS = "list_users"
    KICK_USER = "kick_user"
    BAN_USER = "ban_user"
    
    # Status
    SUCCESS = "success"
    ERROR = "error"
    NOTIFICATION = "notification"
    
    # CTF/Flags
    FLAG_SUBMIT = "flag_submit"
    FLAG_REQUEST = "flag_request"
    FLAG_RESPONSE = "flag_response"
```

### User Roles

```python
class UserRole(Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
```

### Functions

#### `create_message(msg_type: MessageType, data: dict) -> dict`
Create a standardized message with timestamp.

#### `serialize_message(message: dict) -> bytes`
Serialize message to bytes (length + JSON).

#### `deserialize_message(data: bytes) -> Tuple[Optional[dict], bytes]`
Parse bytes, handling partial messages.

#### `hash_password(password: str) -> str`
SHA256 hash for password storage.

---

## Client Components

### ChatClient

Main client orchestrator.

```python
client = ChatClient()
client.connect(host, port, username)
client.send_message("Hello!")
client.display_flags()
```

### ConnectionManager

Handles socket communication.

```python
conn = ConnectionManager()
conn.connect("localhost", 8891)
conn.send_data(message)
data = conn.receive_data()
```

### RoomManager

Manages room operations.

```python
rooms = RoomManager(conn)
rooms.join("general")
rooms.create("private_room", "private", "password")
rooms.list_rooms()
```

### MessageHandler

Processes incoming messages.

```python
handler = MessageHandler(flag_detector, conn, notifier)
handler.handle(message, current_room)
```

### FlagDetector

Detects CTF flags in messages.

```python
detector = FlagDetector()
flags = detector.detect("Found flag{secret}")
detector.store_flag("flag{secret}", "username", "general", "message")
```

---

## Server Components

### ChatServer

Main server class.

```python
server = ChatServer(host="0.0.0.0", port=8891)
server.start()  # Blocking call
```

### ClientHandler

Manages client connections on server.

```python
# Internally used by ChatServer
handler.register_client(username, socket, addr, role)
handler.send_to_client(username, msg_type, data)
handler.broadcast_to_room(room_manager, room, msg_type, data)
```

### ServerRoomManager

Manages room state on server.

```python
rooms = ServerRoomManager()
rooms.create_room("chat", RoomType.PUBLIC, "")
rooms.add_user_to_room("alice", "chat")
rooms.ban_user("bob", "chat")
```

---

## Utilities

### EmojiAliases

Text-to-emoji conversion.

```python
text = EmojiAliases.replace("I love this :heart: :fire:")
# Returns: "I love this ❤️ 🔥:"
```

### NotificationManager

Cross-platform system notifications.

```python
notifier = NotificationManager()
notifier.notify_flag_found(flag, "username")
notifier.subscribe(callback_function)
```

---

## Exceptions

```python
from drevoid.common.exceptions import (
    DrevoidException,      # Base exception
    ConnectionException,   # Connection errors
    AuthenticationException,  # Auth failures
    RoomException,        # Room operation errors
)
```

---

## Logger

```python
from drevoid.common.logging import Logger

logger = Logger()
logger.info("Information")
logger.success("Operation succeeded")
logger.warning("Warning message")
logger.error("Error occurred")
logger.debug("Debug info")
```
