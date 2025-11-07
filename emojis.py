import re
from typing import Dict, List, Tuple

class EmojiAliases:
    _BASE_ALIASES: Dict[str, str] = {
        "heart": "❤️", "love": "❤️", "sparkling_heart": "💖", "broken_heart": "💔", "two_hearts": "💕",
        "kiss": "😘", "heart_eyes": "😍", "hug": "🤗", "smile": "😊", "happy": "😁", "grin": "😄",
        "laugh": "😆", "joy": "😂", "wink": "😉", "blush": "☺️", "relieved": "😌", "cool": "😎",
        "thinking": "🤔", "mindblown": "🤯", "shock": "😲", "surprised": "😮", "plead": "🥺",
        "cry": "😢", "sob": "😭", "sad": "😞", "angry": "😠", "rage": "😡", "mad": "🤬",
        "tired": "😩", "sleepy": "😴", "fear": "😨", "scream": "😱", "confused": "😕", "worried": "😟",
        "neutral": "😐", "expressionless": "😑", "grimace": "😬", "smirk": "😏", "halo": "😇",
        "nerd": "🤓", "monocle": "🧐", "ghost": "👻", "clown": "🤡", "poop": "💩", "robot": "🤖",
        "sick": "🤢", "vomit": "🤮", "mask": "😷", "yawn": "🥱", "sleep": "😴", "dizzy": "😵",
        "relaxed": "😌", "facepalm": "🤦", "shrug": "🤷", "eyeroll": "🙄", "cool_face": "🆒",
        "thumbsup": "👍", "thumbsdown": "👎", "ok": "👌", "ok_hand": "👌", "clap": "👏", "pray": "🙏",
        "wave": "👋", "fist": "✊", "peace": "✌️", "crossed_fingers": "🤞", "point_up": "☝️",
        "point_down": "👇", "point_left": "👈", "point_right": "👉", "call_me": "🤙",
        "muscle": "💪", "writing": "✍️", "nail_polish": "💅", "handshake": "🤝",
        "raised_hands": "🙌", "tada": "🎉", "flex": "💪",
        "sun": "☀️", "moon": "🌙", "star": "⭐", "spark": "✨", "sparkles": "✨", "fire": "🔥",
        "rain": "🌧️", "snow": "❄️", "zap": "⚡", "leaf": "🍃", "seedling": "🌱", "earth": "🌎",
        "dog": "🐶", "cat": "🐱", "lion": "🦁", "tiger": "🐯", "panda": "🐼", "bear": "🐻",
        "unicorn": "🦄", "rabbit": "🐰", "monkey": "🐒", "frog": "🐸", "bird": "🐦", "bee": "🐝",
        "butterfly": "🦋", "fish": "🐠", "whale": "🐋", "dolphin": "🐬",
        "pizza": "🍕", "burger": "🍔", "fries": "🍟", "hotdog": "🌭", "taco": "🌮", "burrito": "🌯",
        "sushi": "🍣", "ramen": "🍜", "cake": "🎂", "cookie": "🍪", "donut": "🍩", "icecream": "🍦",
        "coffee": "☕", "tea": "🍵", "beer": "🍺", "wine": "🍷", "cocktail": "🍸",
        "clinking_glasses": "🥂", "popcorn": "🍿", "chocolate": "🍫", "apple": "🍎", "banana": "🍌",
        "computer": "💻", "laptop": "💻", "phone": "📱", "call": "📞", "mail": "✉️", "calendar": "📅",
        "clock": "⏰", "camera": "📷", "video": "🎬", "lightbulb": "💡", "gear": "⚙️", "hammer": "🔨",
        "wrench": "🔧", "shield": "🛡️", "key": "🔑", "lock": "🔒", "unlock": "🔓", "link": "🔗",
        "bug": "🐛", "code": "💻", "cybersec": "🔐", "terminal": "🖥️", "rocket": "🚀",
        "satellite": "🛰️", "robot_face": "🤖",
        "music": "🎵", "guitar": "🎸", "drum": "🥁", "microphone": "🎤", "film": "🎞️",
        "game": "🎮", "dice": "🎲", "trophy": "🏆", "medal": "🎖️", "star_struck": "🤩",
        "book": "📚", "pen": "🖊️", "paint": "🎨", "art": "🖼️", "gift": "🎁", "flag": "🚩",
        "map": "🗺️", "globe": "🌍", "pin": "📌", "fireworks": "🎆", "party": "🥳",
        "megaphone": "📣", "speaker": "🔊", "bell": "🔔", "mute": "🔇", "mailbox": "📫",
        "chart": "📈", "money": "💰", "coin": "🪙", "wallet": "👛", "shopping": "🛒",
        "crown": "👑", "ring": "💍", "gem": "💎",
        "warning": "⚠️", "info": "ℹ️", "check": "✅", "cross": "❌", "100": "💯",
        "boom": "💥", "hourglass": "⌛", "hourglass_flowing_sand": "⏳",
        "question": "❓", "exclamation": "❗", "infinity": "♾️", "peace_symbol": "☮️",
        "recycle": "♻️", "atom": "⚛️", "om": "🕉️", "yin_yang": "☯️", "skull": "💀"
    }

    _SYNONYMS: Dict[str, List[str]] = {
        "heart": ["heart", "love", "two_hearts", "sparkling_heart", "broken_heart"],
        "thumbsup": ["thumbsup", "like", "ok", "ok_hand", "good"],
        "thumbsdown": ["thumbsdown", "dislike", "bad"],
        "laugh": ["laugh", "lol", "joy", "haha"],
        "cry": ["cry", "sob", "sad", "tears"],
        "angry": ["angry", "mad", "rage"],
        "party": ["party", "yay", "celebrate", "tada"],
        "hacker": ["hacker", "bot", "robot", "cybersec"],
        "cool": ["cool", "sunglasses", "chill"],
        "shock": ["shock", "mindblown", "surprised", "wow"],
        "fear": ["fear", "scream", "scared"],
        "happy": ["smile", "happy", "grin", "wink", "blush", "relieved"],
        "fire": ["fire", "lit", "hot"],
        "100": ["100", "one_hundred", "perfect"]
    }

    def __init__(self):
        self.aliases: Dict[str, str] = dict(self._BASE_ALIASES)
        for canonical, syns in self._SYNONYMS.items():
            emoji = self.aliases.get(canonical)
            if emoji:
                for s in syns:
                    self.aliases[s] = emoji
        self._lower_aliases = {k.lower(): v for k, v in self.aliases.items()}
        self._pattern, self._group_count = self._compile_pattern()

    def _compile_pattern(self) -> Tuple[re.Pattern, int]:
        keys = sorted(map(re.escape, self._lower_aliases.keys()), key=len, reverse=True)
        joined = "|".join(keys)
        pattern = re.compile(rf":({joined}):", re.IGNORECASE)
        return pattern, len(keys)

    def replace(self, content: str) -> str:
        if not content:
            return content
        def _repl(m: re.Match) -> str:
            k = m.group(1).lower()
            return self._lower_aliases.get(k, m.group(0))
        return self._pattern.sub(_repl, content)

    def add_alias(self, key: str, emoji: str, synonyms: List[str] = None):
        if not key or not emoji:
            return
        self.aliases[key] = emoji
        if synonyms:
            for s in synonyms:
                self.aliases[s] = emoji
        self._lower_aliases = {k.lower(): v for k, v in self.aliases.items()}
        self._pattern, self._group_count = self._compile_pattern()

    def list_aliases(self) -> str:
        emoji_map: Dict[str, List[str]] = {}
        for k, e in sorted(self.aliases.items()):
            emoji_map.setdefault(e, []).append(k)
        lines: List[str] = []
        for emoji, keys in sorted(emoji_map.items(), key=lambda x: -len(x[1])):
            lines.append(f"{emoji}  {', '.join(sorted(set([f':{k}:' for k in keys])))}")
        return "\n".join(lines)

EmojiAliasesInstance = EmojiAliases()
