#!/usr/bin/env python3
"""Test authentication flow - CONNECT then JOIN_ROOM."""

import socket
import json
import sys
import time
import threading

# Add src to path
sys.path.insert(0, "src")

from drevoid.core.protocol import (
    create_message,
    serialize_message,
    deserialize_message,
    MessageType,
)


def start_test_server():
    """Start server in background."""
    from drevoid.server.server import ChatServer
    
    server = ChatServer(host="127.0.0.1", port=5555)
    server.start()


def test_auth_flow():
    """Test CONNECT -> JOIN_ROOM flow."""
    time.sleep(1)  # Wait for server to start
    
    try:
        # Connect to server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5555))
        print("✅ Connected to server")
        
        # Send CONNECT
        connect_msg = create_message(MessageType.CONNECT, {"username": "jhon"})
        sock.send(serialize_message(connect_msg))
        print("📤 Sent CONNECT message")
        
        # Receive response
        response_data = sock.recv(4096)
        response, _ = deserialize_message(response_data)
        print(f"📥 Received: {response}")
        
        if response.get("type") != MessageType.SUCCESS.value:
            print("❌ CONNECT failed")
            return False
        
        print("✅ CONNECT successful")
        
        # Send JOIN_ROOM
        join_msg = create_message(MessageType.JOIN_ROOM, {"room_name": "general", "password": ""})
        sock.send(serialize_message(join_msg))
        print("📤 Sent JOIN_ROOM message")
        
        # Receive response
        response_data = sock.recv(4096)
        response, _ = deserialize_message(response_data)
        print(f"📥 Received: {response}")
        
        if response.get("type") == MessageType.ERROR.value:
            print(f"❌ JOIN_ROOM failed: {response.get('data', {}).get('message')}")
            return False
        
        print("✅ JOIN_ROOM successful")
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=start_test_server, daemon=True)
    server_thread.start()
    
    # Run test
    success = test_auth_flow()
    sys.exit(0 if success else 1)
