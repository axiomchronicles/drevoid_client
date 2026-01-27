"""Client application entry point."""

import os
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

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


def main():
    """Main entry point."""
    try:
        os.system("cls" if os.name == "nt" else "clear")
        show_banner()

        client = ChatClient()
        shell = ChatShell(client)
        client.shell = shell

        # Auto-connect if arguments provided
        if len(sys.argv) >= 4:
            host = sys.argv[1]
            try:
                port = int(sys.argv[2])
                username = sys.argv[3]

                print(f"{colorize('🔄 Auto-connecting...', Colors.YELLOW)}")
                if client.connect(host, port, username):
                    print(f"{colorize('✅ Connected successfully!', Colors.GREEN)}")
                    shell.update_prompt()
                else:
                    print(f"{colorize('❌ Auto-connect failed', Colors.RED)}")
            except ValueError:
                print(f"{colorize('❌ Invalid port in arguments', Colors.RED)}")

        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print(f"\n{colorize('👋 Interrupted by user', Colors.YELLOW)}")
        except EOFError:
            print(f"\n{colorize('👋 Goodbye!', Colors.YELLOW)}")

    except Exception as e:
        print(f"{colorize('❌ Application error:', Colors.RED)} {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean shutdown
        if "client" in locals():
            try:
                client.disconnect()
            except Exception:
                pass


if __name__ == "__main__":
    main()
