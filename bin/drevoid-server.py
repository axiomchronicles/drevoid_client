"""Server application entry point."""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from drevoid.server.server import ChatServer


def main():
    """Main entry point for server."""
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
