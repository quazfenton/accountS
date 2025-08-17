import os
import platform
import subprocess
from datetime import datetime

# Cross-platform notification support
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

class Notifier:
    def __init__(self):
        self.system = platform.system()
        self.log_file = "failures.log"
        
    def send_notification(self, message):
        """Send system notification and log to file"""
        # Log to file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write to log file: {e}")
            
        # Send system notification
        try:
            # Try plyer first (cross-platform)
            if PLYER_AVAILABLE:
                notification.notify(
                    title="Bot Alert",
                    message=message,
                    timeout=5
                )
            # Fallback to system-specific methods
            elif self.system == "Darwin":  # macOS
                subprocess.run(['osascript', '-e', f'display notification "{message}" with title "Bot Alert"'], 
                             check=False, timeout=10)
            elif self.system == "Linux":
                subprocess.run(['notify-send', "Bot Alert", message], 
                             check=False, timeout=10)
            elif self.system == "Windows":
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast("Bot Alert", message, duration=5)
                except ImportError:
                    print(f"Bot Alert: {message}")
            else:
                print(f"Bot Alert: {message}")
        except Exception as e:
            print(f"Failed to send notification: {e}")
            print(f"Bot Alert: {message}")
    
    def human_intervention_required(self, platform, reason, account_data=None):
        """Notify that human intervention is required"""
        message = f"Human intervention required for {platform}: {reason}"
        if account_data:
            message += f"\nAccount: {account_data.get('email', '')}"
        
        self.send_notification(message)
    
    def send_alert(self, message):
        """Send a general alert notification"""
        self.send_notification(f"Alert: {message}")
        
    def log_failure(self, platform, reason, details=None):
        """Log a failure with details"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {platform} failure: {reason}"
        if details:
            log_entry += f"\nDetails: {details}"
        log_entry += "\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)