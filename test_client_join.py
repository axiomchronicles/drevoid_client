#!/usr/bin/env python3
"""Interactive test of the client - JoinRoom flow."""

import sys
import time

sys.path.insert(0, "src")

from drevoid.client.chat_client import ChatClient

def test_client_join():
    """Test client connection and joining room."""
    client = ChatClient()
    
    # Connect (default port is 8891)
    if not client.connect("127.0.0.1", 8891, "test_user"):
        print("❌ Failed to connect")
        return False
    
    print("✅ Connected successfully")
    time.sleep(1)
    
    # Try to join general room
    if not client.room_manager.join("general"):
        print("❌ Failed to join room")
        return False
    
    print("✅ Joined room successfully")
    time.sleep(1)
    
    # Try to send a message
    if not client.send_message("Hello from test!"):
        print("⚠️  Message may have failed to send")
    else:
        print("✅ Message sent")
    
    time.sleep(1)
    client.disconnect()
    print("✅ Disconnected")
    return True


if __name__ == "__main__":
    test_client_join()
