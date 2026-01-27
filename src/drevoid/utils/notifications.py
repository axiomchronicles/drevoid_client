"""Cross-platform notification system."""

import subprocess
import threading
import sys
import time
import shutil
from typing import List, Callable, Dict


class NotificationManager:
    """
    Manages system and terminal notifications.

    Supports Linux (notify-send), macOS (osascript), and Windows (PowerShell).
    Includes callback system and rate limiting to prevent notification spam.
    """

    def __init__(self, enable_system_notifications: bool = True, rate_limit_seconds: float = 1.5):
        """
        Initialize notification manager.

        Args:
            enable_system_notifications: Enable OS-level notifications
            rate_limit_seconds: Minimum seconds between duplicate notifications
        """
        self.callbacks: List[Callable] = []
        self.enable_system_notifications = bool(enable_system_notifications)
        self.rate_limit_seconds = float(rate_limit_seconds)
        self._last_notified: Dict[str, float] = {}
        self._platform = sys.platform
        self._notify_send = shutil.which("notify-send")
        self._osascript = shutil.which("osascript")
        self._powershell = shutil.which("powershell") or shutil.which("pwsh")

    def subscribe(self, callback: Callable) -> None:
        """
        Subscribe to notification events.

        Args:
            callback: Function to call on notifications
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unsubscribe(self, callback: Callable) -> None:
        """
        Unsubscribe from notification events.

        Args:
            callback: Function to remove from subscribers
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def toggle(self, enabled: bool) -> None:
        """
        Toggle system notifications on/off.

        Args:
            enabled: Whether to enable notifications
        """
        self.enable_system_notifications = bool(enabled)

    def notify_flag_found(self, flag, finder_username: str) -> None:
        """
        Notify about a flag discovery.

        Args:
            flag: Flag object that was found
            finder_username: Username of who found it
        """
        payload = {
            "type": "flag_found",
            "flag": flag.content,
            "finder": finder_username,
            "room": flag.room,
            "timestamp": flag.timestamp,
            "preview": flag.message_preview,
        }

        # Call all subscribers
        for cb in list(self.callbacks):
            try:
                cb(payload)
            except Exception:
                pass

        # Check rate limit
        key = f"{flag.content}:{finder_username}:{flag.room}"
        now = time.time()
        last = self._last_notified.get(key, 0)
        if now - last < self.rate_limit_seconds:
            return

        self._last_notified[key] = now

        if self.enable_system_notifications:
            title = f"Flag Found by {finder_username}"
            body = f"{flag.content} in #{flag.room}"
            threading.Thread(
                target=self._send_system_notification,
                args=(title, body),
                daemon=True,
            ).start()
        else:
            try:
                print("\a", end="", flush=True)
            except Exception:
                pass

    def notify_user_message(self, username: str, content: str) -> None:
        """
        Notify about a user message.

        Args:
            username: Username of sender
            content: Message content
        """
        payload = {"type": "user_message", "username": username, "content": content}
        for cb in list(self.callbacks):
            try:
                cb(payload)
            except Exception:
                pass

    def _send_system_notification(self, title: str, message: str) -> None:
        """
        Send notification using platform-specific method.

        Args:
            title: Notification title
            message: Notification message
        """
        try:
            if self._platform.startswith("linux") and self._notify_send:
                subprocess.Popen(
                    [self._notify_send, title, message],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            if self._platform == "darwin" and self._osascript:
                esc_title = title.replace('"', '\\"')
                esc_message = message.replace('"', '\\"')
                subprocess.Popen(
                    [
                        "osascript",
                        "-e",
                        f'display notification "{esc_message}" with title "{esc_title}"',
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return

            if self._platform.startswith("win") and self._powershell:
                safe_title = title.replace('"', '`"').replace("'", "''")
                safe_message = message.replace('"', '`"').replace("'", "''")
                ps_cmd = (
                    f'[Windows.UI.Notifications.ToastNotificationManager, '
                    f'Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; '
                    f'$template = [Windows.UI.Notifications.ToastNotificationManager]'
                    f'::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); '
                    f'$xml = $template.GetXml(); $texts = $xml.GetElementsByTagName("text"); '
                    f'$texts.Item(0).AppendChild($xml.CreateTextNode("{safe_title}")) > $null; '
                    f'$texts.Item(1).AppendChild($xml.CreateTextNode("{safe_message}")) > $null; '
                    f'$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); '
                    f'[Windows.UI.Notifications.ToastNotificationManager]'
                    f'::CreateToastNotifier("Drevoid").Show($toast)'
                )
                subprocess.Popen(
                    [self._powershell, "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
        except Exception:
            pass

        # Fallback to simple bell/print
        try:
            print(f"[NOTIFY] {title}: {message}")
            print("\a", end="", flush=True)
        except Exception:
            pass
