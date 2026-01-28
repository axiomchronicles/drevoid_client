"""
Drevoid CLI - Command-line interface for the Drevoid chat client.

Entry point for the 'dre' command.
"""

import sys
import os
import argparse
from pathlib import Path

from drevoid.client.chat_client import ChatClient
from drevoid.ui.shell import ChatShell
from drevoid.core.protocol import Colors, colorize


def show_banner():
    """Display welcome banner."""
    banner = f"""
{colorize('╔══════════════════════════════════════════════════════════╗', Colors.CYAN)}
{colorize('║', Colors.CYAN)} {colorize('🚀 Drevoid LAN Chat Client', Colors.BOLD + Colors.WHITE)} {' ' * 23} {colorize('║', Colors.CYAN)}
{colorize('║', Colors.CYAN)} {colorize('Terminal-based chat with rooms & private messaging', Colors.WHITE)} {' ' * 7} {colorize('║', Colors.CYAN)}
{colorize('╚══════════════════════════════════════════════════════════╝', Colors.CYAN)}

{colorize('💡 Quick Start:', Colors.YELLOW)}
  1. Type '{colorize('connect', Colors.CYAN)}' to connect to a server
  2. Type '{colorize('help', Colors.CYAN)}' for all available commands
  3. Start chatting in rooms or send private messages!

{colorize('🎯 Pro Tips:', Colors.YELLOW)}
  • Use '{colorize('join general', Colors.CYAN)}' to join the default room
  • Use '{colorize('msg username message', Colors.CYAN)}' for private messages
  • Use '{colorize('create myroom private password123', Colors.CYAN)}' for private rooms
  • Use '{colorize('flags', Colors.CYAN)}' to view all captured CTF flags
"""
    print(banner)


def show_version():
    """Display version information."""
    print(f"{colorize('Drevoid Client', Colors.BOLD + Colors.GREEN)} v1.0.0")
    print("Terminal-based LAN chat with rooms, private messaging, and CTF detection")


def start_client(host=None, port=None, username=None, room=None):
    """
    Start the Drevoid chat client.
    
    Args:
        host: Server hostname (optional, prompted if not provided)
        port: Server port (optional, defaults to 5000)
        username: Username (optional, prompted if not provided)
        room: Room to join on startup (optional)
    """
    try:
        os.system("cls" if os.name == "nt" else "clear")
        show_banner()

        client = ChatClient()
        shell = ChatShell(client)
        client.shell = shell

        # If connection parameters provided, auto-connect
        if host and port and username:
            print(f"\n{colorize('Connecting...', Colors.CYAN)}")
            if client.connect(host, int(port), username):
                print(f"{colorize('✅ Connected!', Colors.GREEN)}")
                if room:
                    client.join_room(room)
            else:
                print(f"{colorize('❌ Connection failed', Colors.RED)}")
                return 1
        
        # Start interactive shell
        shell.cmdloop()
        return 0

    except KeyboardInterrupt:
        print(f"\n{colorize('Goodbye!', Colors.YELLOW)}")
        return 0
    except Exception as e:
        print(f"{colorize('Error:', Colors.RED)} {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="dre",
        description="Drevoid - Terminal-based LAN chat client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{colorize('Examples:', Colors.BOLD)}
  dre                                    # Start interactive client
  dre -H 192.168.1.100 -u alice         # Connect to specific server
  dre -H 192.168.1.100 -p 5000 -u bob   # Connect with custom port
  dre -H 192.168.1.100 -u carol -r dev  # Connect and join room on startup

{colorize('Environment Variables:', Colors.BOLD)}
  DREVOID_HOST    - Default server host
  DREVOID_PORT    - Default server port (default: 5000)
  DREVOID_USER    - Default username
  DREVOID_ROOM    - Default room to join on startup
        """,
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s 1.0.0",
        help="Show version information"
    )

    parser.add_argument(
        "-H", "--host",
        type=str,
        default=os.environ.get("DREVOID_HOST"),
        help="Server hostname or IP address"
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        default=int(os.environ.get("DREVOID_PORT", 5000)),
        help="Server port (default: 5000)"
    )

    parser.add_argument(
        "-u", "--username",
        type=str,
        default=os.environ.get("DREVOID_USER"),
        help="Username to use for connection"
    )

    parser.add_argument(
        "-r", "--room",
        type=str,
        default=os.environ.get("DREVOID_ROOM"),
        help="Room to join on startup"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    # Start client with provided arguments
    return start_client(
        host=args.host,
        port=args.port,
        username=args.username,
        room=args.room,
    )


if __name__ == "__main__":
    sys.exit(main())
