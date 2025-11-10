from typing import Dict, Any, Optional, Union
from pathlib import Path
import json
import os
from dataclasses import dataclass, asdict
import logging
from config.advanced_config import AdvancedConfig

@dataclass
class UnifiedConfig:
    """Unified configuration object"""
    # Database settings
    db_path: str = "accounts.db"
    
    # Proxy settings
    proxies: list = None
    proxy_enabled: bool = False
    
    # Captcha settings
    captcha_services: list = None
    
    # Browser settings
    headless: bool = True
    viewport_width: int = 1366
    viewport_height: int = 768
    
    # Rate limiting
    requests_per_minute: int = 10
    accounts_per_hour: int = 5
    
    # Verification settings
    max_captcha_attempts: int = 3
    sms_timeout: int = 300
    email_verification_timeout: int = 600
    
    def __post_init__(self):
        if self.proxies is None:
            self.proxies = []
        if self.captcha_services is None:
            self.captcha_services = []

class EnhancedConfigManager:
    """Enhanced configuration manager with validation and fallbacks"""
    
    def __init__(self, config_path: str = "config/app_config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with fallbacks"""
        # Start with default configuration
        config = self._get_defaults()
        
        # Load from main config file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge file config with defaults (file config overrides defaults)
                    config = self._deep_merge(config, file_config)
            except Exception as e:
                self.logger.warning(f"Could not load config from {self.config_path}: {e}")
        
        # Load from environment variables (highest priority)
        env_config = self._load_from_env()
        config = self._deep_merge(config, env_config)
        
        return config
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "database": {
                "path": "accounts.db",
                "timeout": 30,
                "connection_pool_size": 10
            },
            "proxy": {
                "enabled": False,
                "list": [],
                "rotation_enabled": True,
                "test_url": "http://httpbin.org/ip",
                "timeout": 10
            },
            "captcha": {
                "services": [],
                "timeout": 120,
                "max_attempts": 3,
                "fallback_enabled": True
            },
            "browser": {
                "headless": True,
                "viewport": {"width": 1366, "height": 768},
                "user_agent_rotation": True,
                "stealth_enabled": True
            },
            "verification": {
                "email_timeout": 600,
                "sms_timeout": 300,
                "max_attempts": 5,
                "human_intervention_threshold": 3
            },
            "rate_limiting": {
                "requests_per_minute": 10,
                "accounts_per_hour": 5,
                "min_delay_between_requests": 2,
                "max_delay_between_requests": 10
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": "logs/app.log"
            }
        }
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        env_config = {}
        
        # Database settings
        db_path = os.getenv('DB_PATH')
        if db_path:
            env_config.setdefault('database', {})['path'] = db_path
            
        db_timeout = os.getenv('DB_TIMEOUT')
        if db_timeout:
            env_config.setdefault('database', {})['timeout'] = int(db_timeout)
        
        # Proxy settings
        proxy_list = os.getenv('PROXY_LIST')
        if proxy_list:
            env_config.setdefault('proxy', {})['list'] = proxy_list.split(',') if proxy_list else []
        
        proxy_enabled = os.getenv('PROXY_ENABLED')
        if proxy_enabled:
            env_config.setdefault('proxy', {})['enabled'] = proxy_enabled.lower() == 'true'
        
        # Captcha settings
        captcha_api_key = os.getenv('CAPTCHA_API_KEY')
        if captcha_api_key:
            services = env_config.setdefault('captcha', {}).setdefault('services', [])
            services.append({
                'name': '2captcha',
                'api_key': captcha_api_key
            })
        
        # Browser settings
        headless = os.getenv('BROWSER_HEADLESS')
        if headless:
            env_config.setdefault('browser', {})['headless'] = headless.lower() == 'true'
        
        # Rate limiting
        rpm = os.getenv('REQUESTS_PER_MINUTE')
        if rpm:
            env_config.setdefault('rate_limiting', {})['requests_per_minute'] = int(rpm)
        
        # Verification
        email_timeout = os.getenv('EMAIL_VERIFICATION_TIMEOUT')
        if email_timeout:
            env_config.setdefault('verification', {})['email_timeout'] = int(email_timeout)
        
        return env_config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries, with override taking precedence"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self):
        """Validate configuration values"""
        try:
            # Validate database settings
            db_config = self.config_data.get('database', {})
            if not isinstance(db_config.get('path'), str):
                raise ValueError("Database path must be a string")
            if not isinstance(db_config.get('timeout', 30), (int, float)):
                raise ValueError("Database timeout must be a number")
            
            # Validate proxy settings
            proxy_config = self.config_data.get('proxy', {})
            if not isinstance(proxy_config.get('list'), list):
                raise ValueError("Proxy list must be an array")
            if not isinstance(proxy_config.get('enabled', False), bool):
                raise ValueError("Proxy enabled must be a boolean")
            
            # Validate rate limiting
            rate_config = self.config_data.get('rate_limiting', {})
            rpm = rate_config.get('requests_per_minute', 10)
            if not isinstance(rpm, int) or not (1 <= rpm <= 100):
                raise ValueError("Requests per minute must be an integer between 1 and 100")
            
            # Validate verification settings
            verify_config = self.config_data.get('verification', {})
            max_attempts = verify_config.get('max_attempts', 5)
            if not isinstance(max_attempts, int) or not (1 <= max_attempts <= 20):
                raise ValueError("Max verification attempts must be an integer between 1 and 20")
            
            email_timeout = verify_config.get('email_timeout', 600)
            if not isinstance(email_timeout, (int, float)) or email_timeout <= 0:
                raise ValueError("Email verification timeout must be a positive number")
            
            self.logger.info("Configuration validation passed")
            
        except ValueError as e:
            self.logger.error(f"Configuration validation error: {e}")
            raise
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config_data.get('database', {})
    
    def get_proxy_config(self) -> Dict[str, Any]:
        """Get proxy configuration"""
        return self.config_data.get('proxy', {})
    
    def get_captcha_config(self) -> Dict[str, Any]:
        """Get captcha configuration"""
        return self.config_data.get('captcha', {})
    
    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration"""
        return self.config_data.get('browser', {})
    
    def get_verification_config(self) -> Dict[str, Any]:
        """Get verification configuration"""
        return self.config_data.get('verification', {})
    
    def get_rate_limiting_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return self.config_data.get('rate_limiting', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config_data.get('logging', {})

# Global configuration instance
def get_config() -> EnhancedConfigManager:
    """Get the global configuration manager instance"""
    return EnhancedConfigManager()

# Backwards compatibility with existing AdvancedConfig
class UnifiedAdvancedConfig(AdvancedConfig):
    """Unified configuration that extends the existing AdvancedConfig with new features"""
    
    def __init__(self, config_file: str = "config/advanced_config.json"):
        super().__init__(config_file)
        self.enhanced_manager = EnhancedConfigManager()
    
    def get_enhanced_config(self) -> EnhancedConfigManager:
        """Get the enhanced configuration manager"""
        return self.enhanced_manager