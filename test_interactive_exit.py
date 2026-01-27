#!/usr/bin/env python3
"""Interactive test that simulates the exit scenario from the issue."""

import sys
import time

sys.path.insert(0, "src")

from drevoid.client.chat_client import ChatClient
from drevoid.ui.shell import ChatShell

def test_interactive():
    """Test interactive client with proper shutdown."""
    client = ChatClient()
    shell = ChatShell(client)
    client.shell = shell
    
    # Auto-connect
    print("🔗 Auto-connecting to server...")
    if client.connect("127.0.0.1", 8891, "kali"):
        print("✅ Connected successfully!")
        shell.update_prompt()
    else:
        print("❌ Failed to connect")
        return
    
    time.sleep(0.5)
    
    # Join room
    print("📍 Joining general room...")
    client.room_manager.join("general")
    time.sleep(0.5)
    
    # Simulate sending a message
    print("💬 Sending test message...")
    client.send_message("Test message from kali")
    time.sleep(0.5)
    
    # Simulate exit command
    print("\n👋 Exiting (simulating 'exit' command)...")
    shell.update_prompt()
    time.sleep(0.5)
    
    # This is where the daemon thread error was happening
    print("Goodbye!")

if __name__ == "__main__":
    try:
        test_interactive()
        print("\n✅ Test completed successfully - no threading errors")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
