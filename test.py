import os
import platform
import subprocess

class NotificationManager:
    @staticmethod
    def notify(title: str, message: str):
        system = platform.system()

        if system == "Darwin":  # macOS
            subprocess.run([
                "osascript",
                "-e",
                f'display notification "{message}" with title "{title}"'
            ])

        elif system == "Linux":
            # Works on most Linux distros with libnotify
            subprocess.run(["notify-send", title, message])

        elif system == "Windows":
            # Use built-in PowerShell Toast Notifications
            powershell_command = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);
            $textNodes = $template.GetElementsByTagName("text");
            $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null;
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null;
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template);
            $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Drevoid LAN Chat");
            $notifier.Show($toast);
            '''
            subprocess.run(["powershell", "-Command", powershell_command], shell=True)

        else:
            print(f"[Notification] {title}: {message}")


if __name__ == "__main__":
    NotificationManager.notify("Test Title", "This is a test notification message.")