import os
import platform
import subprocess
from datetime import datetime

class Notifier:
    def __init__(self):
        self.system = platform.system()
        self.log_file = "failures.log"
        
    def send_notification(self, message):
        """Send system notification and log to file"""
        # Log to file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)
            
        # Send system notification
        if self.system == "Darwin":  # macOS
            subprocess.run(['osascript', '-e', f'display notification "{message}" with title "Bot Alert"'])
        elif self.system == "Linux":
            subprocess.run(['notify-send', "Bot Alert", message])
        elif self.system == "Windows":
            # Requires win10toast, we'll add to requirements later
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast("Bot Alert", message)
            except ImportError:
                pass
    
    def human_intervention_required(self, platform, reason, account_data=None):
        """Notify that human intervention is required"""
        message = f"Human intervention required for {platform}: {reason}"
        if account_data:
            message += f"\nAccount: {account_data.get('email', '')}"
        
        self.send_notification(message)
        
    def log_failure(self, platform, reason, details=None):
        """Log a failure with details"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {platform} failure: {reason}"
        if details:
            log_entry += f"\nDetails: {details}"
        log_entry += "\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)