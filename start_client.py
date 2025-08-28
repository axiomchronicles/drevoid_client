#!/usr/bin/env python3
"""
Client Launcher for Advanced LAN Chat
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from client.client import main

if __name__ == "__main__":
    main()
