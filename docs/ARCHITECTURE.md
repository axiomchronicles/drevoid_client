# Architecture

## Overview

Drevoid is a multi-threaded LAN chat application with a client-server architecture. The design emphasizes clean separation of concerns, thread safety, and extensibility.

## Design Principles

### 1. Separation of Concerns

Each module has a single, well-defined responsibility:

- **`core/`** - Communication protocol and serialization
- **`common/`** - Shared utilities, logging, exceptions
- **`ctf/`** - Flag detection logic
- **`utils/`** - Platform-specific utilities (emojis, notifications)
- **`client/`** - Client-side implementations
- **`server/`** - Server-side implementations
- **`ui/`** - User interface and command shell

### 2. Component Architecture

Each component is independently testable and reusable:

```
ChatClient
├── ConnectionManager (socket handling)
├── RoomManager (room operations)
├── MessageHandler (message processing)
│   └── FlagDetector (flag detection)
├── NotificationManager (system notifications)
└── EmojiAliases (emoji conversion)

ChatServer
├── ClientHandler (client tracking)
├── ServerRoomManager (room state)
└── Flag storage
```

### 3. Thread Safety

- All shared data structures use `ThreadSafeDict`
- Server uses threads for concurrent client handling
- Client uses daemon thread for receiving messages
- No blocking I/O on main thread

### 4. Protocol Design

```
[Message Format]
┌─────────────┬───────────────┐
│  4 bytes    │   N bytes     │
│  (length)   │   (JSON)      │
└─────────────┴───────────────┘

[JSON Structure]
{
  "type": "message_type",
  "timestamp": 1234567890.123,
  "data": { ... }
}
```

## Data Flow

### Connection Flow

```
Client                              Server
  │                                  │
  ├─── connect(host, port, user) ──→ │
  │                                  ├─ Validate username
  │ ← ─ SUCCESS response ─ ─ ─ ─ ─ ─┤
  │                                  ├─ Send room list
  │ ← ─ Server status ─ ─ ─ ─ ─ ─ ─┤
  │                                  │
```

### Message Flow

```
Client A                             Server                         Client B
  │                                   │                              │
  ├─── message in room ──────────────→ │                              │
  │                                   ├─ Broadcast to room ─────────→ │
  │                                   │  (exclude sender)            │
  │ ← ─ ─ ─ ─ Notification ─ ─ ─ ─ ─ │                              │
  │                                   │                              │
```

### Flag Detection Flow

```
Message received
      │
      ↓
FlagDetector.detect()
      │
      ├─ Pattern matching
      ├─ Extract flags
      ↓
Flag found?
      │
      ├─ YES: Store flag
      ├─ YES: Notify user
      ├─ YES: Send to server
      │
      └─ NO: Continue
```

## Server Architecture

### Request Handling

```
Client Connection
      │
      ├─ New thread created
      │
      ├─ Wait for messages
      │
      ├─ Deserialize message
      │
      ├─ Route by type
      │   ├─ CONNECT → Register client
      │   ├─ JOIN_ROOM → Room operations
      │   ├─ MESSAGE → Broadcast
      │   ├─ FLAG_SUBMIT → Store flag
      │   └─ ...
      │
      ├─ Process request
      │
      ├─ Send response
      │
      └─ Handle disconnect
```

## Client Architecture

### Message Processing

```
Main Thread (User Input)
      │
      ├─ Read command
      ├─ Process locally or send to server
      └─ Display prompt

Receive Thread (Background)
      │
      ├─ Wait for data from socket
      ├─ Buffer incomplete messages
      ├─ Deserialize complete messages
      ├─ Route to MessageHandler
      ├─ Display via callbacks
      └─ Update prompt
```

## Extension Points

### Adding New Message Type

1. Add to `MessageType` enum in `core/protocol.py`
2. Implement handler in `ServerRoomManager` or `ClientHandler`
3. Add command to `ChatShell` if user-facing

Example:
```python
# In core/protocol.py
class MessageType(Enum):
    # ... existing types ...
    CUSTOM_ACTION = "custom_action"

# In server/server.py
def _process_message(...):
    elif msg_type == MessageType.CUSTOM_ACTION.value:
        self._handle_custom_action(username, data)

def _handle_custom_action(self, username, data):
    # Implementation
    pass

# In ui/shell.py
def do_custom_command(self, args):
    """User-facing command"""
    message = create_message(MessageType.CUSTOM_ACTION, {...})
    self.client.connection_manager.send_data(message)
```

### Adding New Flag Pattern

```python
# In ctf/flag_patterns.py
class FlagPattern(Enum):
    # ... existing patterns ...
    CUSTOM_FORMAT = r'custom\[.*?\]'

# Automatically detected by FlagDetector
```

### Adding Platform Support

```python
# In utils/notifications.py
def _send_system_notification(self, title, message):
    # Add new platform check
    if self._platform == "newos":
        # Custom notification logic
        pass
```

## Performance Considerations

### Scalability
- Threading allows handling 100+ concurrent clients
- Room capacity configurable (default 50)
- ThreadSafeDict uses RLock for minimal contention

### Memory
- Messages buffered efficiently with struct packing
- Flag storage uses dictionary (O(1) lookup)
- Client history pruned as needed

### Network
- Binary frame format minimizes payload
- Rate limiting on notifications prevents spam
- Efficient broadcast uses set operations

## Security

### Password Protection
- SHA256 hashing for private room passwords
- No plaintext storage

### Input Validation
- Username checked for duplicates
- Message content validated before broadcast
- Role-based access control for moderation

### Thread Safety
- All shared mutable state protected by locks
- No race conditions on connection/disconnection
- Atomic flag operations
