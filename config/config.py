import json
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class PlatformConfig:
    name: str
    url: str
    registration_path: str
    username_field: str
    password_field: str
    submit_button: str
    success_selector: str
    failure_selector: str

class Config:
    def __init__(self, config_file_path: str = "config/settings.json"):
        self.config_file_path = config_file_path
        self.config_data = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from a JSON file"""
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file_path}")
            
        with open(self.config_file_path, 'r') as file:
            return json.load(file)
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key"""
        return self.config_data.get(key, default)
        
    def get_platform_config(self, platform_name: str) -> PlatformConfig:
        """Get configuration for specific platform"""
        platform_configs = {
            'twitter': PlatformConfig(
                name='twitter',
                signup_url='https://twitter.com/i/flow/signup',
                selectors={
                    'name': 'input[name="name"]',
                    'email': 'input[name="email"]',
                    'next': 'div[role="button"]:has-text("Next")',
                    'code_input': 'input[name="verification_code"]'
                },
                success_indicators=['text=Welcome to Twitter', 'text=What's happening'],
                error_indicators=['text=Something went wrong', 'text=Try again'],
                verification_types=[VerificationType.SMS, VerificationType.EMAIL],
                rate_limit_delay=(5, 15)
            ),
            'facebook': PlatformConfig(
                name='facebook',
                signup_url='https://www.facebook.com/reg/',
                selectors={
                    'first_name': 'input[name="firstname"]',
                    'last_name': 'input[name="lastname"]',
                    'email': 'input[name="reg_email__"]',
                    'password': 'input[name="reg_passwd__"]',
                    'birthday_day': 'select[name="birthday_day"]',
                    'birthday_month': 'select[name="birthday_month"]',
                    'birthday_year': 'select[name="birthday_year"]',
                    'submit': 'button[name="websubmit"]'
                },
                success_indicators=['text=Welcome to Facebook', 'text=Find friends'],
                error_indicators=['text=Please fix the following errors', 'text=This email is already registered'],
                verification_types=[VerificationType.SMS, VerificationType.RECAPTCHA],
                rate_limit_delay=(10, 25)
            ),
            'instagram': PlatformConfig(
                name='instagram',
                signup_url='https://www.instagram.com/accounts/emailsignup/',
                selectors={
                    'email': 'input[name="emailOrPhone"]',
                    'full_name': 'input[name="fullName"]',
                    'username': 'input[name="username"]',
                    'password': 'input[name="password"]',
                    'submit': 'button[type="submit"]'
                },
                success_indicators=['text=Welcome to Instagram', 'text=Find people to follow'],
                error_indicators=['text=This username isn't available', 'text=Please enter a valid email'],
                verification_types=[VerificationType.SMS, VerificationType.EMAIL],
                rate_limit_delay=(8, 20)
            )
        }
        
        if platform_name not in platform_configs:
            raise ValueError(f"Platform {platform_name} not configured")
        
        return platform_configs[platform_name]
        
    def get_verification_config(self) -> Dict[str, Any]:
        """Get verification solver configuration"""
        return self.config_data.get('verification', {})
        
    def get_proxy_config(self) -> Dict[str, Any]:
        """Get proxy configuration"""
        return self.config_data.get('proxy', {})
        
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self.config_data.get('monitoring', {})