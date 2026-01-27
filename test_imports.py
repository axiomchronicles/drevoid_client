#!/usr/bin/env python3
"""Quick test script to verify the application works."""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from drevoid.core.protocol import (
    MessageType, UserRole, RoomType,
    create_message, serialize_message, deserialize_message
)
from drevoid.server.server import ChatServer
from drevoid.client.chat_client import ChatClient

print("✅ All imports successful")
print("\nTesting protocol...")

# Test message creation
msg = create_message(MessageType.CONNECT, {"username": "testuser"})
print(f"✅ Created message: {msg['type']}")

# Test serialization
data = serialize_message(msg)
print(f"✅ Serialized to {len(data)} bytes")

# Test deserialization
parsed, remaining = deserialize_message(data)
print(f"✅ Deserialized: {parsed['type']}")

print("\n✅ All tests passed!")
