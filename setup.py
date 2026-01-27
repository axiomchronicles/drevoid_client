#!/usr/bin/env python3
"""
Setup script for Drevoid application.

Initializes the environment and makes the application ready to run.
"""

import os
import sys
from pathlib import Path


def setup():
    """Setup the application environment."""
    print("🚀 Setting up Drevoid Application...")

    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)

    print("✅ Python version check passed")

    # Create necessary directories
    dirs_to_create = [
        "logs",
        "data",
        "config",
        "tests",
    ]

    for dir_name in dirs_to_create:
        path = Path(__file__).parent / dir_name
        path.mkdir(exist_ok=True)
        print(f"✅ Created {dir_name} directory")

    # Make scripts executable
    scripts = [
        "bin/drevoid-client.py",
        "bin/drevoid-server.py",
    ]

    for script in scripts:
        path = Path(__file__).parent / script
        if path.exists():
            os.chmod(path, 0o755)
            print(f"✅ Made {script} executable")

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("  1. Start server: python bin/drevoid-server.py")
    print("  2. Start client: python bin/drevoid-client.py")
    print("  3. Type 'help' in client for command reference")


if __name__ == "__main__":
    setup()
