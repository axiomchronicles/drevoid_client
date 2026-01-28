# Drevoid - Terminal-Based LAN Chat Client

A professional, feature-rich terminal-based chat application with room management, private messaging, CTF flag detection, and real-time collaboration capabilities.

## Features

✨ **Core Chat Features**
- Multi-room chat system with public and private rooms
- Direct private messaging between users
- Real-time message delivery and synchronization
- User presence tracking and status updates
- Persistent room history

🔐 **Security & Privacy**
- Password-protected private rooms
- User authentication and role-based access control
- Message encryption support
- Admin console for server management
- User ban/kick/mute capabilities

🚩 **CTF Integration**
- Automatic CTF flag detection and capture
- Flag pattern matching (flag format: `flag{...}`)
- Flag statistics and leaderboard
- Integration with HackTheBox and similar platforms

👥 **User Management**
- User roles: Admin, Moderator, User
- Room creation and management
- User muting/unmuting by admins
- Connection status monitoring
- User profile customization

🎯 **Productivity**
- Command-line interface with intuitive commands
- Interactive shell with command history
- Help system with detailed documentation
- Color-coded output for better readability
- Support for both IPv4 and IPv6

## Installation

### From PyPI (Recommended)

```bash
pip install drevoid-client
```

### From Source

```bash
git clone https://github.com/axiomchronicles/drevoid_client.git
cd drevoid_client
pip install -e .
```

### Requirements

- Python 3.10 or higher
- No external dependencies (uses only Python standard library)

## Quick Start

### Starting the Client

The simplest way to start Drevoid is to use the `dre` command:

```bash
# Interactive mode
dre

# Connect to a specific server
dre -H 192.168.1.100 -u alice

# Connect with custom port
dre -H 192.168.1.100 -p 5000 -u bob

# Connect and join a room on startup
dre -H 192.168.1.100 -u carol -r development
```

### Command-Line Options

```
usage: dre [-h] [-v] [-H HOST] [-p PORT] [-u USERNAME] [-r ROOM] [--debug]

options:
  -h, --help            Show this help message
  -v, --version         Show version information
  -H, --host HOST       Server hostname or IP address
  -p, --port PORT       Server port (default: 5000)
  -u, --username USERNAME
                        Username to use for connection
  -r, --room ROOM       Room to join on startup
  --debug               Enable debug mode for troubleshooting
```

### Environment Variables

You can set default connection parameters using environment variables:

```bash
export DREVOID_HOST=192.168.1.100
export DREVOID_PORT=5000
export DREVOID_USER=alice
export DREVOID_ROOM=general

# Now you can simply run:
dre
```

## Client Commands

### Connection Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `connect` | `connect` | Connect to a server (prompted for host/port/username) |
| `disconnect` | `disconnect` | Disconnect from the current server |
| `status` | `status` | Show connection status |

### Room Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `join` | `join <room_name>` | Join an existing room |
| `leave` | `leave` | Leave the current room |
| `create` | `create <name> [public\|private] [password]` | Create a new room |
| `rooms` | `rooms` | List all available rooms |
| `users` | `users` | List users in current room |
| `invite` | `invite <username>` | Invite user to current room |
| `topic` | `topic <new_topic>` | Set or update room topic |

### Messaging Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `msg` | `msg <username> <message>` | Send private message to user |
| `reply` | `reply <message>` | Reply to last private message |
| `broadcast` | `broadcast <message>` | Send message to all users |
| `announce` | `announce <message>` | Send announcement to current room |

### User Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `profile` | `profile` | View your profile |
| `setname` | `setname <new_name>` | Change your display name |
| `setstatus` | `setstatus <status>` | Set your status message |
| `whoami` | `whoami` | Show current username |
| `online` | `online` | List all online users |

### CTF Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `flags` | `flags` | Display all captured flags |
| `flag-stats` | `flag-stats` | Show flag statistics |
| `leaderboard` | `leaderboard` | Show flag leaderboard |
| `my-flags` | `my-flags` | Show your captured flags |

### Admin Commands (Admin Only)

| Command | Syntax | Description |
|---------|--------|-------------|
| `kick` | `kick <username> [reason]` | Kick user from room |
| `ban` | `ban <username> [reason]` | Ban user from server |
| `unban` | `unban <username>` | Unban user |
| `mute` | `mute <username> [duration]` | Mute user in current room |
| `unmute` | `unmute <username>` | Unmute user |
| `promote` | `promote <username> [role]` | Promote user to role |
| `demote` | `demote <username>` | Demote user |
| `clearroom` | `clearroom` | Clear all messages in room |
| `lockroom` | `lockroom` | Lock room (no new joins) |
| `unlockroom` | `unlockroom` | Unlock room |

### Utility Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| `help` | `help [command]` | Show help for all or specific command |
| `clear` | `clear` | Clear screen |
| `history` | `history` | Show command history |
| `export` | `export <filename>` | Export chat history |
| `settings` | `settings` | Show current settings |
| `exit` | `exit` | Close application |

## Usage Examples

### Basic Chat Workflow

```bash
# Start client
dre

# At the prompt, connect to a server
> connect
Server host: 192.168.1.100
Server port [5000]: 
Username: alice

# Join a room
> join general

# Send a message (automatic in current room)
> Hello everyone!

# Send private message
> msg bob Hi Bob, how are you?

# View room users
> users

# Leave room
> leave

# Disconnect
> disconnect
```

### Room Management

```bash
# Create a private room
> create dev-team private mysecretpass

# Join the room
> join dev-team

# View room topic
> topic Team Development Discussion

# Invite another user
> invite alice

# Leave when done
> leave
```

### CTF Hunting

```bash
# View all captured flags
> flags

# Check flag statistics
> flag-stats

# View leaderboard
> leaderboard

# See only your flags
> my-flags
```

### Admin Tasks

```bash
# Mute a disruptive user for 30 minutes
> mute spambot 30m

# Kick a user from the current room
> kick baduser "Violated community guidelines"

# Promote a trusted user to moderator
> promote trustworthy moderator

# Ban a user from the entire server
> ban malicious "Spam and harassment"

# Unban a user later
> unban reformed_user
```

## Architecture

### Project Structure

```
drevoid_client/
├── src/drevoid/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point
│   ├── client/
│   │   ├── chat_client.py     # Main client logic
│   │   ├── connection.py      # Network connection management
│   │   ├── message_handler.py # Message routing
│   │   └── room_manager.py    # Room state management
│   ├── core/
│   │   └── protocol.py        # Protocol definitions
│   ├── ui/
│   │   ├── shell.py           # Interactive shell
│   │   └── ui_components.py   # UI helper functions
│   ├── ctf/
│   │   ├── flag_detector.py   # Flag detection logic
│   │   └── flag_patterns.py   # CTF flag patterns
│   ├── common/
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── logging.py         # Logging utilities
│   └── utils/
│       ├── emoji_aliases.py   # Emoji support
│       └── notifications.py   # Notification system
├── bin/
│   ├── drevoid-client.py      # Legacy client entry point
│   └── drevoid-server.py      # Legacy server entry point
├── setup.py                   # Package configuration
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

### Key Components

**ChatClient** (`client/chat_client.py`)
- Manages connection to server
- Handles message sending/receiving
- Maintains local state for rooms and users
- Coordinates with message handler for notifications

**ChatShell** (`ui/shell.py`)
- Interactive command-line interface
- Command parsing and execution
- Help system and command history
- User input handling

**MessageHandler** (`client/message_handler.py`)
- Routes incoming messages
- Processes server notifications
- Updates local room state
- Triggers UI updates

**RoomManager** (`client/room_manager.py`)
- Manages local room state
- Tracks room members
- Handles room-specific operations
- Maintains room history

**FlagDetector** (`ctf/flag_detector.py`)
- Scans messages for CTF flags
- Validates flag format
- Maintains flag statistics
- Integrates with leaderboard

## Configuration

### Config File

Create `~/.drevoid/config.json` for persistent settings:

```json
{
  "theme": "dark",
  "color_output": true,
  "auto_reconnect": true,
  "reconnect_delay": 5,
  "log_level": "INFO",
  "default_host": "192.168.1.100",
  "default_port": 5000,
  "default_username": "alice",
  "ctf_enabled": true,
  "flag_patterns": [
    "flag{.*}",
    "FLAG{.*}",
    "flag\\[.*\\]"
  ]
}
```

### Logging

Logs are written to `~/.drevoid/logs/`:

```
~/.drevoid/
├── config.json
├── logs/
│   ├── client.log
│   └── chat_history.log
└── cache/
    └── flags.json
```

## Development

### Running from Source

```bash
# Clone the repository
git clone https://github.com/axiomchronicles/drevoid_client.git
cd drevoid_client

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Run client
dre
```

### Project Dependencies

Drevoid uses only Python standard library modules:
- `socket` - Networking
- `threading` - Concurrency
- `json` - Message serialization
- `cmd` - Interactive shell
- `struct` - Binary data packing
- `hashlib` - Password hashing
- `time` - Timestamps
- `os` - System operations
- `sys` - System parameters

### Code Style

Follow PEP 8 guidelines:

```bash
# Check code style
python -m flake8 src/

# Format code
python -m black src/

# Type checking
python -m mypy src/
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to server
```bash
# Solution: Verify server is running and port is correct
dre -H <server_ip> -p <port> -u <username>

# Check if port is accessible
telnet 192.168.1.100 5000
```

**Problem**: "Unknown command" errors
```bash
# Solution: Try the `help` command
> help
> help <command>
```

### Message Issues

**Problem**: Messages not sending
```
> Make sure you're connected: status
> Make sure you're in a room: rooms
> Try joining a room: join general
```

**Problem**: Missing private messages
```
> Check if user is online: online
> Try sending again: msg username message
```

### Flag Detection

**Problem**: Flags not being detected
```
> Check flag format matches pattern
> Verify CTF mode is enabled: settings
> Add custom patterns to config
```

## Performance Tips

1. **Large Chat Histories**: Export old messages to free memory
   ```bash
   > export chat_history_2024.txt
   ```

2. **Multiple Rooms**: Reduce number of joined rooms for better performance

3. **Network Optimization**: Use server closest to your location

4. **Message Filtering**: Use room-specific topics to filter conversations

## Security Considerations

1. **Password Protection**: Always use strong passwords for private rooms
2. **Private Messages**: Use for sensitive conversations
3. **Admin Access**: Only promote trusted users to admin role
4. **Ban/Kick**: Remove disruptive users immediately
5. **Flag Sharing**: Be careful when sharing flag information

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions:

- **GitHub Issues**: [Report a bug](https://github.com/axiomchronicles/drevoid_client/issues)
- **Discussions**: [Start a discussion](https://github.com/axiomchronicles/drevoid_client/discussions)
- **Email**: dev@drevoid.local

## Acknowledgments

- Built with Python standard library (no external dependencies)
- Inspired by professional chat systems and CTF platforms
- Community feedback and contributions

## Changelog

### Version 1.0.0 (Current)
- Initial release
- Multi-room chat system
- Private messaging
- CTF flag detection
- Admin console
- CLI integration

---

**Made with ❤️ by the Drevoid Team**

For more information, visit [GitHub Repository](https://github.com/axiomchronicles/drevoid_client)
