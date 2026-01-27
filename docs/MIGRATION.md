# Migration Guide: Old to New Structure

## Overview

The codebase has been restructured to follow professional Python project standards:

- **Better organization**: Clear separation of concerns
- **Improved maintainability**: Modular, testable components
- **Production-ready**: Proper package structure and documentation
- **Extensible**: Easy to add new features

## Directory Structure Changes

### Before
```
drevoid_client/
├── client.py
├── server.py
├── protocol.py
├── notification.py
├── emojis.py
└── ...
```

### After
```
drevoid_client/
├── src/drevoid/           # Main package
│   ├── core/              # Protocol layer
│   ├── client/            # Client components
│   ├── server/            # Server components
│   ├── ui/                # User interface
│   ├── ctf/               # Flag detection
│   ├── common/            # Shared utilities
│   └── utils/             # Helper modules
├── bin/                   # Entry points
├── docs/                  # Documentation
├── tests/                 # Test suites
└── config/                # Configuration
```

## Module Mapping

### Old → New

| Old File | New Location | Notes |
|----------|--------------|-------|
| `protocol.py` | `src/drevoid/core/protocol.py` | Core protocol, serialization |
| `client.py` | `src/drevoid/client/chat_client.py` | Main client class |
| (client components) | `src/drevoid/client/` | Split into multiple modules |
| `server.py` | `src/drevoid/server/server.py` | Main server class |
| (server components) | `src/drevoid/server/` | Split into multiple modules |
| `notification.py` | `src/drevoid/utils/notifications.py` | Notifications |
| `emojis.py` | `src/drevoid/utils/emoji_aliases.py` | Emoji handling |
| (none) | `src/drevoid/ctf/flag_detector.py` | Flag detection |
| `start_client.py` | `bin/drevoid-client.py` | Client entry point |
| (none) | `bin/drevoid-server.py` | Server entry point |

## Code Changes

### Import Statements

**Before:**
```python
from protocol import MessageType, create_message
from notification import NotificationManager
from emojis import EmojiAliasesInstance
```

**After:**
```python
from drevoid.core.protocol import MessageType, create_message
from drevoid.utils.notifications import NotificationManager
from drevoid.utils.emoji_aliases import EmojiAliases
```

### Running Applications

**Before:**
```bash
python client.py
python server.py
```

**After:**
```bash
python bin/drevoid-client.py
python bin/drevoid-server.py

# Or after adding to PATH:
drevoid-client
drevoid-server
```

### Class Names

**Before:**
```python
from client import ChatClient
from protocol import MessageType
```

**After:**
```python
from drevoid.client.chat_client import ChatClient
from drevoid.core.protocol import MessageType
```

## Migration Steps

### For Users

1. Update your imports to use `drevoid` package
2. Use new entry points in `bin/` directory
3. All functionality remains the same, just better organized

### For Developers

1. Read `docs/ARCHITECTURE.md` for design overview
2. Review `docs/API.md` for API reference
3. Follow project structure when adding new features
4. Use type hints and docstrings consistently

## Feature Compatibility

All existing features are fully supported:

- ✅ Multi-room chat
- ✅ Private messaging
- ✅ Flag detection
- ✅ Emoji support
- ✅ Moderation commands
- ✅ Cross-platform notifications
- ✅ Admin console

## Backward Compatibility

Old code modules are preserved in root directory during transition. They will be deprecated after a transition period.

## Questions?

See `docs/ARCHITECTURE.md` and `docs/API.md` for detailed information.
