import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProxyConfig:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    
    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

@dataclass
class CaptchaServiceConfig:
    name: str
    api_key: str
    endpoint: str
    timeout: int = 120
    max_retries: int = 3

class AdvancedConfig:
    def __init__(self, config_file: str = "config/advanced_config.json"):
        self.config_file = config_file
        self.data = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file with fallback to defaults"""
        default_config = {
            "proxies": [],
            "captcha_services": [
                {
                    "name": "2captcha",
                    "api_key": "",
                    "endpoint": "http://2captcha.com/in.php",
                    "timeout": 120,
                    "max_retries": 3
                }
            ],
            "browser_settings": {
                "headless": True,
                "viewport_width": 1366,
                "viewport_height": 768,
                "user_agent_rotation": True,
                "fingerprint_spoofing": True
            },
            "rate_limiting": {
                "requests_per_minute": 10,
                "accounts_per_hour": 5,
                "cooldown_between_accounts": 300
            },
            "verification_settings": {
                "max_captcha_attempts": 3,
                "sms_timeout": 300,
                "email_verification_timeout": 600,
                "human_intervention_threshold": 3
            },
            "identity_generation": {
                "name_sources": ["common_names.json", "generated_names.json"],
                "username_patterns": ["firstname_lastname", "firstname_numbers", "random_words"],
                "password_complexity": "high",
                "email_domains": ["gmail.com", "yahoo.com", "outlook.com"]
            },
            "monitoring": {
                "success_rate_threshold": 0.7,
                "failure_alert_count": 5,
                "log_level": "INFO",
                "metrics_collection": True
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **loaded_config}
            except Exception as e:
                print(f"Error loading config file: {e}, using defaults")
                return default_config
        else:
            # Create default config file
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def _validate_config(self):
        """Validate configuration values"""
        required_sections = ["browser_settings", "rate_limiting", "verification_settings"]
        for section in required_sections:
            if section not in self.data:
                raise ValueError(f"Missing required config section: {section}")
    
    @property
    def proxies(self) -> List[ProxyConfig]:
        """Get configured proxies as ProxyConfig objects"""
        proxy_configs = []
        for proxy_data in self.data.get('proxies', []):
            if isinstance(proxy_data, str):
                # Simple format: "host:port"
                host, port = proxy_data.split(':')
                proxy_configs.append(ProxyConfig(host=host, port=int(port)))
            elif isinstance(proxy_data, dict):
                # Full format with auth
                proxy_configs.append(ProxyConfig(**proxy_data))
        return proxy_configs
    
    @property
    def captcha_services(self) -> List[CaptchaServiceConfig]:
        """Get configured captcha services"""
        services = []
        for service_data in self.data.get('captcha_services', []):
            services.append(CaptchaServiceConfig(**service_data))
        return services
    
    @property
    def browser_settings(self) -> Dict[str, Any]:
        return self.data.get('browser_settings', {})
    
    @property
    def rate_limiting(self) -> Dict[str, Any]:
        return self.data.get('rate_limiting', {})
    
    @property
    def verification_settings(self) -> Dict[str, Any]:
        return self.data.get('verification_settings', {})
    
    @property
    def identity_generation(self) -> Dict[str, Any]:
        return self.data.get('identity_generation', {})
    
    @property
    def monitoring(self) -> Dict[str, Any]:
        return self.data.get('monitoring', {})
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent from the configured list"""
        user_agents = self.data.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ])
        import random
        return random.choice(user_agents)
    
    def update_config(self, section: str, key: str, value: Any):
        """Update a configuration value and save to file"""
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
        self.save_config()
    
    def save_config(self):
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_email_domains(self) -> List[str]:
        """Get list of email domains for account creation"""
        return self.identity_generation.get('email_domains', ['gmail.com', 'yahoo.com', 'outlook.com'])
    
    def get_username_patterns(self) -> List[str]:
        """Get username generation patterns"""
        return self.identity_generation.get('username_patterns', ['firstname_lastname', 'firstname_numbers'])
    
    def should_use_proxy(self) -> bool:
        """Check if proxy usage is enabled and proxies are available"""
        return len(self.proxies) > 0
    
    def get_success_rate_threshold(self) -> float:
        """Get the minimum acceptable success rate"""
        return self.monitoring.get('success_rate_threshold', 0.7)