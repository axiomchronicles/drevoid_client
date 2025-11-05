import subprocess
import threading
import sys
import time
import shutil
from typing import List, Callable, Dict

class NotificationManager:
    def __init__(self, enable_system_notifications: bool = True, rate_limit_seconds: float = 1.5):
        self.callbacks: List[Callable] = []
        self.enable_system_notifications = bool(enable_system_notifications)
        self.rate_limit_seconds = float(rate_limit_seconds)
        self._last_notified: Dict[str, float] = {}
        self._platform = sys.platform
        self._notify_send = shutil.which("notify-send")
        self._osascript = shutil.which("osascript")
        self._powershell = shutil.which("powershell") or shutil.which("pwsh")

    def subscribe(self, callback: Callable):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unsubscribe(self, callback: Callable):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def toggle(self, enabled: bool):
        self.enable_system_notifications = bool(enabled)

    def notify_flag_found(self, flag, finder_username: str):
        payload = {
            "type": "flag_found",
            "flag": flag.content,
            "finder": finder_username,
            "room": flag.room,
            "timestamp": flag.timestamp,
            "preview": flag.message_preview
        }
        for cb in list(self.callbacks):
            try:
                cb(payload)
            except Exception:
                pass
        key = f"{flag.content}:{finder_username}:{flag.room}"
        now = time.time()
        last = self._last_notified.get(key, 0)
        if now - last < self.rate_limit_seconds:
            return
        self._last_notified[key] = now
        if self.enable_system_notifications:
            title = f"Flag Found by {finder_username}"
            body = f"{flag.content} in #{flag.room}"
            threading.Thread(target=self._send_system_notification, args=(title, body), daemon=True).start()
        else:
            try:
                print("\a", end="", flush=True)
            except Exception:
                pass

    def notify_user_message(self, username: str, content: str):
        payload = {"type": "user_message", "username": username, "content": content}
        for cb in list(self.callbacks):
            try:
                cb(payload)
            except Exception:
                pass

    def _send_system_notification(self, title: str, message: str):
        try:
            if self._platform.startswith("linux") and self._notify_send:
                subprocess.Popen([self._notify_send, title, message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            if self._platform == "darwin" and self._osascript:
                esc_title = title.replace('"', '\\"')
                esc_message = message.replace('"', '\\"')
                subprocess.Popen(["osascript", "-e", f'display notification "{esc_message}" with title "{esc_title}"'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            if self._platform.startswith("win") and self._powershell:
                safe_title = title.replace('"', '`"').replace("'", "''")
                safe_message = message.replace('"', '`"').replace("'", "''")
                ps = f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $xml = $template.GetXml(); $texts = $xml.GetElementsByTagName("text"); $texts.Item(0).AppendChild($xml.CreateTextNode("{safe_title}")) > $null; $texts.Item(1).AppendChild($xml.CreateTextNode("{safe_message}")) > $null; $toast = [Windows.UI.Notifications.ToastNotification]::new($xml); [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Drevoid").Show($toast)'
                subprocess.Popen([self._powershell, "-NoProfile", "-NonInteractive", "-Command", ps], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
        except Exception:
            pass
        try:
            print(f"[NOTIFY] {title}: {message}")
            print("\a", end="", flush=True)
        except Exception:
            pass
