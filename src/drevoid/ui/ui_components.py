"""Enhanced UI components for better visual presentation."""

from typing import List, Optional
from ..core.protocol import Colors, colorize


class UIBox:
    """Creates decorative boxes for UI elements."""
    
    @staticmethod
    def header(title: str, width: int = 80) -> str:
        """Create a header box with title."""
        padding = (width - len(title) - 2) // 2
        top = "═" * width
        middle = f"║{' ' * padding}{colorize(title, Colors.BOLD)}{' ' * (width - len(title) - 2 - padding)}║"
        return f"\n{colorize(top, Colors.BLUE)}\n{middle}\n{colorize(top, Colors.BLUE)}"
    
    @staticmethod
    def section(title: str, color: str = Colors.YELLOW) -> str:
        """Create a section header."""
        return f"\n{colorize(f'┌─ {title}', color)} {colorize('─' * (70 - len(title)), Colors.GRAY)}"
    
    @staticmethod
    def item(text: str, level: int = 1) -> str:
        """Create an indented item."""
        indent = "  " * level
        return f"{indent}{colorize('•', Colors.CYAN)} {text}"
    
    @staticmethod
    def separator(width: int = 80) -> str:
        """Create a horizontal separator."""
        return colorize("─" * width, Colors.GRAY)
    
    @staticmethod
    def stat_row(label: str, value: str, label_color: str = Colors.CYAN) -> str:
        """Create a formatted stat row."""
        return f"  {colorize(label, label_color):<30} {colorize(value, Colors.GREEN)}"
    
    @staticmethod
    def table_header(columns: List[str], widths: List[int]) -> str:
        """Create a formatted table header."""
        header = ""
        for col, width in zip(columns, widths):
            header += f"{col:<{width}} "
        return colorize(header, Colors.BOLD + Colors.CYAN)
    
    @staticmethod
    def table_row(values: List[str], widths: List[int]) -> str:
        """Create a formatted table row."""
        row = ""
        for val, width in zip(values, widths):
            row += f"{str(val):<{width}} "
        return row


class StatusIndicator:
    """Various status indicators for UI."""
    
    SUCCESS = colorize("✅", Colors.GREEN)
    ERROR = colorize("❌", Colors.RED)
    WARNING = colorize("⚠️", Colors.YELLOW)
    INFO = colorize("ℹ️", Colors.BLUE)
    FLAG = colorize("🚩", Colors.HIGHLIGHT + Colors.GREEN)
    USER = colorize("👤", Colors.CYAN)
    ADMIN = colorize("👑", Colors.RED)
    MOD = colorize("⭐", Colors.YELLOW)
    LOCK = colorize("🔒", Colors.RED)
    UNLOCK = colorize("🔓", Colors.GREEN)
    LOADING = colorize("⏳", Colors.YELLOW)
    MESSAGE = colorize("💬", Colors.PURPLE)
    PRIVATE = colorize("📩", Colors.PURPLE)
    NOTIFICATION = colorize("📢", Colors.YELLOW)
    CLOCK = colorize("🕐", Colors.GRAY)
    HEART = colorize("❤️", Colors.RED)
    LINK = colorize("🔗", Colors.BLUE)


class CommandHelp:
    """Enhanced command help formatter."""
    
    @staticmethod
    def format_command(cmd: str, args: str, description: str, examples: Optional[List[str]] = None) -> str:
        """Format a command with full help."""
        output = f"\n{colorize('Command:', Colors.BOLD + Colors.CYAN)} {colorize(cmd, Colors.WHITE)}"
        output += f"\n{colorize('Usage:', Colors.YELLOW)}   {colorize(args, Colors.GREEN)}"
        output += f"\n{colorize('Description:', Colors.YELLOW)} {description}"
        
        if examples:
            output += f"\n{colorize('Examples:', Colors.YELLOW)}"
            for example in examples:
                output += f"\n  {colorize('→', Colors.CYAN)} {colorize(example, Colors.GRAY)}"
        
        return output


class Progress:
    """Progress display utilities."""
    
    @staticmethod
    def bar(current: int, total: int, width: int = 40, label: str = "") -> str:
        """Create a progress bar."""
        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100
        
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        
        label_str = f"{label} " if label else ""
        return f"{label_str}{colorize(bar, Colors.GREEN)} {percentage:.0f}%"
    
    @staticmethod
    def spinner_frames() -> List[str]:
        """Get spinner animation frames."""
        return [
            colorize("⠋", Colors.YELLOW),
            colorize("⠙", Colors.YELLOW),
            colorize("⠹", Colors.YELLOW),
            colorize("⠸", Colors.YELLOW),
            colorize("⠼", Colors.YELLOW),
            colorize("⠴", Colors.YELLOW),
            colorize("⠦", Colors.YELLOW),
            colorize("⠧", Colors.YELLOW),
            colorize("⠇", Colors.YELLOW),
            colorize("⠏", Colors.YELLOW),
        ]


class UserDisplay:
    """Utilities for displaying user information."""
    
    @staticmethod
    def format_user(username: str, role: str = "user", is_moderator: bool = False) -> str:
        """Format user with role indicator."""
        if role == "admin":
            icon = StatusIndicator.ADMIN
            color = Colors.RED
        elif is_moderator:
            icon = StatusIndicator.MOD
            color = Colors.YELLOW
        else:
            icon = StatusIndicator.USER
            color = Colors.CYAN
        
        return f"{icon} {colorize(username, color)}"
    
    @staticmethod
    def format_users_list(users: List[dict]) -> str:
        """Format a list of users for display."""
        output = f"\n{colorize('👥 Users in room:', Colors.BOLD + Colors.CYAN)}"
        
        # Sort by role: admin first, then moderators, then users
        sorted_users = sorted(
            users,
            key=lambda u: (u.get("role") != "admin", not u.get("is_moderator", False), u.get("username", ""))
        )
        
        for user in sorted_users:
            output += f"\n  {UserDisplay.format_user(user.get('username', '?'), user.get('role', 'user'), user.get('is_moderator', False))}"
        
        return output


class RoomDisplay:
    """Utilities for displaying room information."""
    
    @staticmethod
    def format_room(room: dict) -> str:
        """Format a single room for display."""
        protection = StatusIndicator.LOCK if room.get("password_protected") else StatusIndicator.UNLOCK
        room_type = room.get("type", "public").upper()
        users_info = f"{room.get('users', 0)}/{room.get('max_users', '?')}"
        
        return (
            f"  {protection} {colorize(room.get('name', '?'), Colors.CYAN)} "
            f"{colorize(f'[{room_type}]', Colors.GRAY)} "
            f"{colorize(f'{users_info} users', Colors.WHITE)}"
        )
    
    @staticmethod
    def format_rooms_list(rooms: List[dict]) -> str:
        """Format a list of rooms for display."""
        output = f"\n{colorize('🏠 Available Rooms:', Colors.BOLD + Colors.CYAN)}"
        
        for room in rooms:
            output += f"\n{RoomDisplay.format_room(room)}"
        
        return output


class FlagDisplay:
    """Utilities for displaying flag information."""
    
    @staticmethod
    def format_flag(flag, index: int = 0) -> str:
        """Format a single flag for display."""
        from ..core.protocol import format_timestamp
        
        output = f"\n  {StatusIndicator.FLAG} {colorize(f'Flag #{index}', Colors.BOLD + Colors.GREEN)}"
        output += f"\n     {colorize('Content:', Colors.YELLOW)} {colorize(flag.content, Colors.HIGHLIGHT + Colors.GREEN)}"
        output += f"\n     {colorize('Found by:', Colors.YELLOW)}   {colorize(flag.finder, Colors.CYAN)}"
        output += f"\n     {colorize('Room:', Colors.YELLOW)}      {colorize(f'#{flag.room}', Colors.BLUE)}"
        output += f"\n     {StatusIndicator.CLOCK} {format_timestamp(flag.timestamp)}"
        output += f"\n     {colorize('Context:', Colors.YELLOW)}   {flag.message_preview[:60]}"
        
        return output
    
    @staticmethod
    def format_flags_list(flags: List) -> str:
        """Format a list of flags for display."""
        if not flags:
            return f"\n{colorize('No flags found yet.', Colors.GRAY)}"
        
        output = f"\n{colorize('🚩 Captured Flags:', Colors.BOLD + Colors.YELLOW + Colors.HIGHLIGHT)}"
        output += f"\n{colorize('Total:', Colors.CYAN)} {len(flags)}"
        
        for idx, flag in enumerate(flags, 1):
            output += FlagDisplay.format_flag(flag, idx)
        
        return output


class MenuBar:
    """Create formatted menu bars."""
    
    @staticmethod
    def quick_commands() -> str:
        """Display quick command menu."""
        commands = [
            ("connect", "Connect to server"),
            ("join", "Join a room"),
            ("flags", "Show captured flags"),
            ("status", "Show connection status"),
            ("help", "Show all commands"),
        ]
        
        output = f"\n{colorize('⚡ Quick Commands:', Colors.BOLD + Colors.YELLOW)}"
        for cmd, desc in commands:
            output += f"\n  {colorize(cmd, Colors.CYAN):12} → {desc}"
        
        return output
    
    @staticmethod
    def connection_info(username: str, room: Optional[str], connected: bool) -> str:
        """Display connection info bar."""
        if not connected:
            return f"{colorize('●', Colors.RED)} {colorize('Not connected', Colors.RED)}"
        
        room_str = f" in {colorize(f'#{room}', Colors.BLUE)}" if room else " {no room}"
        return f"{colorize('●', Colors.GREEN)} {colorize(username, Colors.CYAN)}{room_str}"
