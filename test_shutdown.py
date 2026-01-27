#!/usr/bin/env python3
"""Test clean client shutdown without daemon thread errors."""

import sys
import time
import threading

sys.path.insert(0, "src")

from drevoid.client.chat_client import ChatClient

def test_clean_shutdown():
    """Test that shutdown is clean without threading errors."""
    print("🔄 Creating client...")
    client = ChatClient()
    
    print("🔗 Connecting to server...")
    if not client.connect("127.0.0.1", 8891, "test_user"):
        print("❌ Failed to connect")
        return False
    
    print("✅ Connected")
    time.sleep(0.5)
    
    print("📍 Joining room...")
    if not client.room_manager.join("general"):
        print("❌ Failed to join")
        return False
    
    print("✅ Joined room")
    time.sleep(0.5)
    
    print("💬 Sending message...")
    client.send_message("Test message")
    time.sleep(0.5)
    
    print("🔌 Disconnecting...")
    client.disconnect()
    time.sleep(0.5)
    
    print("✅ Shutdown complete - no errors expected above")
    return True

if __name__ == "__main__":
    try:
        success = test_clean_shutdown()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
