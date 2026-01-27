"""Emoji alias management system."""

from typing import Dict, List


class EmojiAliases:
    """
    Manages emoji substitution using text aliases.

    Converts text patterns like :heart: to emoji characters
    for terminal-based chat messaging.
    """

    _BASE_ALIASES: Dict[str, str] = {
        "heart": "❤️",
        "love": "❤️",
        "sparkling_heart": "💖",
        "broken_heart": "💔",
        "two_hearts": "💕",
        "kiss": "😘",
        "heart_eyes": "😍",
        "hug": "🤗",
        "smile": "😊",
        "happy": "😁",
        "grin": "😄",
        "laugh": "😆",
        "joy": "😂",
        "wink": "😉",
        "blush": "☺️",
        "relieved": "😌",
        "cool": "😎",
        "thinking": "🤔",
        "mindblown": "🤯",
        "shock": "😲",
        "surprised": "😮",
        "plead": "🥺",
        "cry": "😢",
        "sob": "😭",
        "sad": "😞",
        "angry": "😠",
        "rage": "😡",
        "mad": "🤬",
        "tired": "😩",
        "sleepy": "😴",
        "fear": "😨",
        "scream": "😱",
        "confused": "😕",
        "worried": "😟",
        "neutral": "😐",
        "expressionless": "😑",
        "grimace": "😬",
        "smirk": "😏",
        "halo": "😇",
        "nerd": "🤓",
        "monocle": "🧐",
        "ghost": "👻",
        "clown": "🤡",
        "poop": "💩",
        "robot": "🤖",
        "sick": "🤢",
        "vomit": "🤮",
        "mask": "😷",
        "yawn": "🥱",
        "sleep": "😴",
        "dizzy": "😵",
        "relaxed": "😌",
        "facepalm": "🤦",
        "shrug": "🤷",
        "eyeroll": "🙄",
        "cool_face": "🆒",
        "thumbsup": "👍",
        "thumbsdown": "👎",
        "ok": "👌",
        "ok_hand": "👌",
        "clap": "👏",
        "pray": "🙏",
        "wave": "👋",
        "fist": "✊",
        "peace": "✌️",
        "crossed_fingers": "🤞",
        "point_up": "☝️",
        "point_down": "👇",
        "point_left": "👈",
        "point_right": "👉",
        "call_me": "🤙",
        "muscle": "💪",
        "writing": "✍️",
        "nail_polish": "💅",
        "handshake": "🤝",
        "raised_hands": "🙌",
        "tada": "🎉",
        "flex": "💪",
        "sun": "☀️",
        "moon": "🌙",
        "star": "⭐",
        "spark": "✨",
        "sparkles": "✨",
        "fire": "🔥",
        "rain": "🌧️",
        "snow": "❄️",
        "zap": "⚡",
        "leaf": "🍃",
        "seedling": "🌱",
        "earth": "🌎",
        "dog": "🐶",
        "cat": "🐱",
        "lion": "🦁",
        "tiger": "🐯",
        "panda": "🐼",
        "bear": "🐻",
        "unicorn": "🦄",
        "rabbit": "🐰",
        "monkey": "🐒",
        "frog": "🐸",
        "bird": "🐦",
        "bee": "🐝",
        "butterfly": "🦋",
        "fish": "🐠",
        "whale": "🐋",
        "dolphin": "🐬",
        "pizza": "🍕",
        "burger": "🍔",
        "fries": "🍟",
        "hotdog": "🌭",
        "taco": "🌮",
        "burrito": "🌯",
        "sushi": "🍣",
        "ramen": "🍜",
        "cake": "🎂",
        "cookie": "🍪",
        "donut": "🍩",
        "icecream": "🍦",
        "coffee": "☕",
        "tea": "🍵",
        "beer": "🍺",
        "wine": "🍷",
        "cocktail": "🍸",
        "clinking_glasses": "🥂",
        "popcorn": "🍿",
        "chocolate": "🍫",
        "apple": "🍎",
        "banana": "🍌",
        "computer": "💻",
        "laptop": "💻",
        "phone": "📱",
        "call": "📞",
        "mail": "✉️",
        "calendar": "📅",
        "clock": "⏰",
        "camera": "📷",
        "video": "🎬",
        "lightbulb": "💡",
        "gear": "⚙️",
        "hammer": "🔨",
        "wrench": "🔧",
        "shield": "🛡️",
        "key": "🔑",
        "lock": "🔒",
        "unlock": "🔓",
        "link": "🔗",
        "bug": "🐛",
        "code": "💻",
        "cybersec": "🔐",
        "terminal": "🖥️",
        "rocket": "🚀",
        "satellite": "🛰️",
        "robot_face": "🤖",
        "music": "🎵",
        "guitar": "🎸",
        "drum": "🥁",
        "microphone": "🎤",
        "film": "🎞️",
        "game": "🎮",
        "dice": "🎲",
        "trophy": "🏆",
        "medal": "🎖️",
        "star_struck": "🤩",
        "book": "📚",
        "pen": "🖊️",
        "paint": "🎨",
        "art": "🖼️",
        "gift": "🎁",
        "flag": "🚩",
        "map": "🗺️",
        "globe": "🌍",
        "pin": "📌",
        "fireworks": "🎆",
        "party": "🥳",
        "megaphone": "📣",
        "speaker": "🔊",
        "bell": "🔔",
        "mute": "🔇",
        "mailbox": "📫",
        "chart": "📈",
        "money": "💰",
        "coin": "🪙",
        "wallet": "👛",
        "shopping": "🛒",
        "crown": "👑",
        "ring": "💍",
        "gem": "💎",
        "warning": "⚠️",
        "info": "ℹ️",
        "check": "✅",
        "cross": "❌",
        "100": "💯",
        "boom": "💥",
        "hourglass": "⌛",
        "hourglass_flowing_sand": "⏳",
        "question": "❓",
        "exclamation": "❗",
        "infinity": "♾️",
        "peace_symbol": "☮️",
        "recycle": "♻️",
        "atom": "⚛️",
        "om": "🕉️",
        "yin_yang": "☯️",
        "skull": "💀",
    }

    _SYNONYMS: Dict[str, List[str]] = {
        "heart": ["heart", "love", "two_hearts", "sparkling_heart", "broken_heart"],
        "thumbsup": ["thumbsup", "like", "ok", "ok_hand", "good"],
        "fire": ["fire", "hot", "lit"],
        "rocket": ["rocket", "launch"],
        "tada": ["tada", "celebration", "party"],
    }

    @classmethod
    def replace(cls, text: str) -> str:
        """
        Replace emoji aliases in text with actual emoji characters.

        Format: :alias_name:
        Example: "I love this :heart: :fire: :rocket:"

        Args:
            text: Text containing emoji aliases

        Returns:
            Text with aliases replaced by emojis
        """
        result = text
        for alias, emoji in cls._BASE_ALIASES.items():
            pattern = f":{alias}:"
            result = result.replace(pattern, emoji)
        return result

    @classmethod
    def list_aliases(cls) -> str:
        """
        Get formatted list of all available aliases.

        Returns:
            Formatted string of aliases grouped by category
        """
        lines = []
        aliases_sorted = sorted(cls._BASE_ALIASES.items())

        for i in range(0, len(aliases_sorted), 3):
            chunk = aliases_sorted[i : i + 3]
            row = "  "
            for alias, emoji in chunk:
                row += f":{alias:20s} {emoji}  "
            lines.append(row)

        return "\n".join(lines)
