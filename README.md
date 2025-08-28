# Drevoid LAN Chat Application

A robust terminal-based LAN chat application built with Python sockets, featuring Drevoid room management, private messaging, and an interactive command shell.

## 🚀 Features

### Core Features
- **Multi-user support** - Handle multiple concurrent users
- **Room management** - Create and join public/private rooms
- **Private messaging** - Send direct messages to specific users
- **Interactive shell** - Command-based interface using Python's `cmd` module
- **Real-time messaging** - Instant message delivery
- **User authentication** - Username-based connection system

### Drevoid Features
- **Public & Private Rooms** - Create password-protected private rooms
- **Room moderation** - Kick and ban users (for moderators)
- **Message history** - Last 10 messages shown when joining rooms
- **User roles** - Admin, Moderator, and User roles
- **Connection management** - Robust connection handling and reconnection
- **Colorized interface** - ANSI color codes for better UX
- **Server commands** - Administrative server management
- **Thread-safe operations** - Safe concurrent access to shared resources

## 📁 Project Structure

```
drevoid/
├── server/
│   ├── __init__.py
│   └── server.py          # Main server implementation
├── client/
│   ├── __init__.py
│   └── client.py          # Interactive client with cmd shell
├── common/
│   ├── __init__.py
│   └── protocol.py        # Shared protocol and utilities
├── docs/
│   └── API.md            # API documentation
├── start_server.py       # Server launcher
├── start_client.py       # Client launcher
└── README.md            # This file
```

## 🏃‍♂️ Quick Start

### 1. Start the Server
```bash
python start_server.py
# or with custom host/port
python start_server.py 0.0.0.0 8080
```

### 2. Start the Client
```bash
python start_client.py
# or with auto-connect
python start_client.py localhost 12345 myusername
```

### 3. Basic Usage
```
# Connect to server
> connect localhost 12345 myusername

# Join the general room
> join general

# Send a message
> Hello everyone!

# Create a private room
> create myroom private mypassword

# Send private message
> msg username Hey there!

# List available commands
> help
```

## 🎯 Commands Reference

### Connection Commands
- `connect [host] [port] [username]` - Connect to server
- `disconnect` - Disconnect from server
- `quit/exit` - Exit the application

### Room Management
- `join <room_name> [password]` - Join a room
- `leave` - Leave current room
- `create <room_name> [private] [password]` - Create a room
- `rooms` - List available rooms
- `users` - List users in current room

### Messaging
- `<message>` - Send message to current room
- `msg <username> <message>` - Send private message
- `pm <username> <message>` - Send private message (alias)

### Moderation (Moderators only)
- `kick <username>` - Kick user from room
- `ban <username>` - Ban user from room

### Utility
- `status` - Show connection status
- `clear` - Clear screen
- `help` - Show all commands

## 🖥️ Server Commands

While the server is running, you can use these commands:

- `help` - Show server commands
- `stats` - Show server statistics
- `users` - List connected users
- `rooms` - List active rooms
- `shutdown` - Shutdown server

## 🛠️ Technical Details

### Architecture
- **Server**: Multi-threaded server handling concurrent connections
- **Client**: Event-driven client with separate threads for sending/receiving
- **Protocol**: JSON-based message protocol with length prefixing
- **Threading**: Thread-safe data structures and proper synchronization

### Message Types
- `CONNECT/DISCONNECT` - Connection management
- `MESSAGE` - Room messages
- `PRIVATE_MESSAGE` - Direct messages
- `JOIN_ROOM/LEAVE_ROOM` - Room management
- `CREATE_ROOM` - Room creation
- `LIST_ROOMS/LIST_USERS` - Information queries
- `KICK_USER/BAN_USER` - Moderation actions
- `NOTIFICATION` - System notifications
- `SUCCESS/ERROR` - Response messages

### Security Features
- Password hashing for room protection
- User role management
- Ban/kick functionality
- Input validation and sanitization

## 🎨 Customization

### Adding New Commands
1. Add new message type to `common/protocol.py`
2. Implement handler in `server/server.py`
3. Add command method to client shell in `client/client.py`

### Extending Room Features
- Modify the `Room` class in `server/server.py`
- Add new room properties and methods
- Update client commands as needed

## 🚧 System Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
- Terminal with ANSI color support (optional, for colors)

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Feel free to fork this project and submit pull requests for improvements!

## 🐛 Troubleshooting

### Common Issues

**Connection refused**
- Check if server is running
- Verify host and port settings
- Check firewall settings

**Messages not appearing**
- Ensure you're connected and in a room
- Check network connectivity
- Restart client if needed

**Permission denied errors**
- Check user roles and permissions
- Ensure you're a moderator for kick/ban commands

### Debug Mode
Add debug prints in the code to trace message flow and connection issues.
