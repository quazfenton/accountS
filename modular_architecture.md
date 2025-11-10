# Modular Architecture Improvements for Mass Account Creation Automator

## Overview

The current architecture has tight coupling between modules and lacks proper interface abstractions. This document outlines the modular architecture improvements needed to make the system more maintainable, testable, and extensible.

## 1. Abstract Service Interfaces

### 1.1 Abstract Verification Service

```python
# File: interfaces/verification_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class VerificationResult:
    success: bool
    verification_code: Optional[str] = None
    error_message: Optional[str] = None
    requires_human_intervention: bool = False

class AbstractVerificationService(ABC):
    """Abstract base class for all verification services"""
    
    @abstractmethod
    async def verify_email(self, email: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Verify email using the service"""
        pass
    
    @abstractmethod
    async def verify_sms(self, phone_number: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Verify SMS using the service"""
        pass
    
    @abstractmethod
    async def solve_captcha(self, captcha_type: str, captcha_context: Dict[str, Any]) -> VerificationResult:
        """Solve captcha using the service"""
        pass
    
    @abstractmethod
    async def verify_2fa(self, method: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Verify 2FA using the service"""
        pass
```

### 1.2 Abstract Proxy Service

```python
# File: interfaces/proxy_service.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ProxyStats:
    success_rate: float
    response_time: float
    is_working: bool
    consecutive_failures: int

class AbstractProxyService(ABC):
    """Abstract base class for proxy services"""
    
    @abstractmethod
    async def get_best_proxy(self) -> Optional[str]:
        """Get the best available proxy based on performance metrics"""
        pass
    
    @abstractmethod
    async def test_proxy(self, proxy: str) -> Tuple[bool, float]:
        """Test if a proxy is working and measure response time"""
        pass
    
    @abstractmethod
    def record_success(self, proxy: str, response_time: float):
        """Record successful use of a proxy"""
        pass
    
    @abstractmethod
    def record_failure(self, proxy: str, response_time: float = None):
        """Record failed use of a proxy"""
        pass
    
    @abstractmethod
    def get_proxy_stats(self) -> Dict[str, ProxyStats]:
        """Get statistics for all managed proxies"""
        pass
```

### 1.3 Abstract Captcha Service

```python
# File: interfaces/captcha_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CaptchaSolution:
    success: bool
    solution: Optional[str] = None
    error_message: Optional[str] = None
    cost: float = 0.0

class AbstractCaptchaService(ABC):
    """Abstract base class for captcha solving services"""
    
    @abstractmethod
    async def solve_recaptcha(self, site_key: str, page_url: str, **kwargs) -> CaptchaSolution:
        """Solve reCAPTCHA"""
        pass
    
    @abstractmethod
    async def solve_hcaptcha(self, site_key: str, page_url: str, **kwargs) -> CaptchaSolution:
        """Solve hCaptcha"""
        pass
    
    @abstractmethod
    async def solve_funcaptcha(self, public_key: str, page_url: str, **kwargs) -> CaptchaSolution:
        """Solve FunCaptcha"""
        pass
    
    @abstractmethod
    async def solve_image_captcha(self, image_data: bytes, **kwargs) -> CaptchaSolution:
        """Solve image-based captcha"""
        pass
    
    @abstractmethod
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics and cost tracking"""
        pass
```

### 1.4 Abstract Email Service

```python
# File: interfaces/email_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class EmailVerificationResult:
    success: bool
    code: Optional[str] = None
    error_message: Optional[str] = None

class AbstractEmailService(ABC):
    """Abstract base class for email services"""
    
    @abstractmethod
    async def get_verification_code(self, email: str, **kwargs) -> EmailVerificationResult:
        """Get verification code from email"""
        pass
    
    @abstractmethod
    async def check_email_exists(self, email: str) -> bool:
        """Check if email exists and is accessible"""
        pass
    
    @abstractmethod
    async def get_recent_emails(self, email: str, since_minutes: int = 5) -> List[Dict[str, Any]]:
        """Get recent emails for the specified email address"""
        pass
```

### 1.5 Abstract Account Manager

```python
# File: interfaces/account_manager.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class AccountCreationResult:
    success: bool
    account_data: Dict[str, Any]
    error_message: Optional[str] = None
    requires_human_intervention: bool = False

class AbstractAccountManager(ABC):
    """Abstract base class for account managers"""
    
    @abstractmethod
    async def create_single_account(self, identity: Dict[str, Any], platforms: List[str]) -> AccountCreationResult:
        """Create a single account across multiple platforms"""
        pass
    
    @abstractmethod
    async def create_accounts_batch(self, identities: List[Dict[str, Any]], platforms: List[str]) -> Dict[str, Any]:
        """Create multiple accounts in batch"""
        pass
    
    @abstractmethod
    async def verify_account(self, account_data: Dict[str, Any]) -> bool:
        """Verify an existing account"""
        pass
    
    @abstractmethod
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get current session statistics"""
        pass
```

## 2. Service Implementations

### 2.1 Concrete Verification Service Implementation

```python
# File: services/concrete_verification_service.py
from interfaces.verification_service import AbstractVerificationService, VerificationResult
from utils.advanced_captcha_solver import AdvancedCaptchaSolver
from modules.advanced_verification_solver import VerificationType
import asyncio
import logging

class ConcreteVerificationService(AbstractVerificationService):
    """Concrete implementation of verification service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.captcha_solver = AdvancedCaptchaSolver()
        self.verification_solver = None  # To be injected
    
    async def verify_email(self, email: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Implement email verification"""
        try:
            # Use injected verification solver or implement directly
            code_result = await self._get_email_verification_code(email)
            
            if code_result['success']:
                return VerificationResult(
                    success=True,
                    verification_code=code_result['code']
                )
            else:
                return VerificationResult(
                    success=False,
                    error_message=code_result['error']
                )
        except Exception as e:
            self.logger.error(f"Email verification error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def verify_sms(self, phone_number: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Implement SMS verification"""
        try:
            # Implementation for SMS verification
            # This would involve getting phone number, requesting code, etc.
            # Placeholder for actual implementation
            return VerificationResult(
                success=False,
                error_message="SMS verification not fully implemented"
            )
        except Exception as e:
            self.logger.error(f"SMS verification error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def solve_captcha(self, captcha_type: str, captcha_context: Dict[str, Any]) -> VerificationResult:
        """Implement captcha solving"""
        try:
            result = await self.captcha_solver.solve_captcha(captcha_type, **captcha_context)
            
            if result['success']:
                return VerificationResult(
                    success=True,
                    verification_code=result['solution']
                )
            else:
                return VerificationResult(
                    success=False,
                    error_message=result.get('error', 'Captcha solving failed')
                )
        except Exception as e:
            self.logger.error(f"Captcha solving error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def verify_2fa(self, method: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Implement 2FA verification"""
        try:
            # Implementation for 2FA verification based on method (TOTP, SMS, etc.)
            return VerificationResult(
                success=False,
                error_message="2FA verification not fully implemented"
            )
        except Exception as e:
            self.logger.error(f"2FA verification error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def _get_email_verification_code(self, email: str) -> Dict[str, Any]:
        """Helper to get email verification code - to be implemented properly"""
        # This is where the actual email verification code extraction logic would go
        # Using IMAP, POP3, or email service APIs
        return {'success': False, 'error': 'Email code extraction not implemented'}
```

### 2.2 Concrete Proxy Service Implementation

```python
# File: services/concrete_proxy_service.py
from interfaces.proxy_service import AbstractProxyService, ProxyStats
from utils.proxy_manager import ImprovedProxyManager
import asyncio

class ConcreteProxyService(AbstractProxyService):
    """Concrete implementation of proxy service"""
    
    def __init__(self, proxies: List[str]):
        self.proxy_manager = ImprovedProxyManager(proxies)
    
    async def get_best_proxy(self) -> Optional[str]:
        """Get the best available proxy"""
        return await self.proxy_manager.get_best_proxy()
    
    async def test_proxy(self, proxy: str) -> Tuple[bool, float]:
        """Test if a proxy is working"""
        return await self.proxy_manager.test_proxy(proxy)
    
    def record_success(self, proxy: str, response_time: float):
        """Record successful use of a proxy"""
        self.proxy_manager.record_success(proxy, response_time)
    
    def record_failure(self, proxy: str, response_time: float = None):
        """Record failed use of a proxy"""
        self.proxy_manager.record_failure(proxy, response_time)
    
    def get_proxy_stats(self) -> Dict[str, ProxyStats]:
        """Get statistics for all managed proxies"""
        raw_stats = self.proxy_manager.get_proxy_stats()
        # Convert to ProxyStats dataclass format
        converted_stats = {}
        for proxy, stats in raw_stats.items():
            converted_stats[proxy] = ProxyStats(
                success_rate=stats['success_rate'],
                response_time=stats['avg_response_time'],
                is_working=stats['success_rate'] > 0.5,  # Consider working if success rate > 50%
                consecutive_failures=stats['consecutive_failures']
            )
        return converted_stats
```

## 3. Dependency Injection Container

### 3.1 Service Registry and Factory

```python
# File: core/service_container.py
from typing import Dict, Type, Any, Optional
from interfaces.verification_service import AbstractVerificationService
from interfaces.proxy_service import AbstractProxyService
from interfaces.captcha_service import AbstractCaptchaService
from interfaces.email_service import AbstractEmailService
from interfaces.account_manager import AbstractAccountManager
from services.concrete_verification_service import ConcreteVerificationService
from services.concrete_proxy_service import ConcreteProxyService

class ServiceContainer:
    """Dependency injection container for services"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._service_classes: Dict[str, Type] = {}
        self._singleton_instances: Dict[str, Any] = {}
    
    def register(self, name: str, service_class: Type, singleton: bool = True):
        """Register a service class"""
        self._service_classes[name] = service_class
        if singleton:
            self._singleton_instances[name] = None
    
    def register_instance(self, name: str, instance: Any):
        """Register a pre-created service instance"""
        self._services[name] = instance
    
    def get(self, name: str) -> Any:
        """Get a service instance"""
        # Check if it's registered as instance
        if name in self._services:
            return self._services[name]
        
        # Check if it's a singleton that needs instantiation
        if name in self._singleton_instances and self._singleton_instances[name] is not None:
            return self._singleton_instances[name]
        
        # Check if class is registered and instantiate
        if name in self._service_classes:
            service_class = self._service_classes[name]
            instance = service_class()  # You may need to pass dependencies here
            
            if name in self._singleton_instances:
                self._singleton_instances[name] = instance
                return instance
            else:
                return instance
        
        raise ValueError(f"Service {name} not registered")
    
    def configure_default_services(self, config_data: Dict[str, Any] = None):
        """Configure default services based on configuration"""
        # Register verification service
        self.register('verification_service', ConcreteVerificationService, singleton=True)
        
        # Register proxy service
        proxy_list = config_data.get('proxies', []) if config_data else []
        # We need to handle the proxy list dependency differently
        self._service_classes['proxy_service'] = lambda: ConcreteProxyService(proxy_list)
    
    def build_account_manager(self) -> AbstractAccountManager:
        """Build account manager with all dependencies injected"""
        # This would build the account manager with all dependencies
        pass

# Global service container instance
container = ServiceContainer()
```

## 4. Updated Account Manager with Dependency Injection

```python
# File: modules/di_account_manager.py
from interfaces.account_manager import AbstractAccountManager, AccountCreationResult
from interfaces.verification_service import AbstractVerificationService
from interfaces.proxy_service import AbstractProxyService
from interfaces.captcha_service import AbstractCaptchaService
from interfaces.email_service import AbstractEmailService
from modules.improved_database import ImprovedDatabase
from utils.identity_generator import IdentityGenerator
from utils.monitoring import MetricsCollector
from typing import Dict, List, Any, Optional
import asyncio
import logging

class DIEnabledAccountManager(AbstractAccountManager):
    """Account manager with dependency injection"""
    
    def __init__(
        self,
        verification_service: AbstractVerificationService,
        proxy_service: AbstractProxyService,
        captcha_service: AbstractCaptchaService,
        email_service: AbstractEmailService,
        database: ImprovedDatabase = None,
        metrics_collector: MetricsCollector = None,
        max_workers: int = 5
    ):
        self.verification_service = verification_service
        self.proxy_service = proxy_service
        self.captcha_service = captcha_service
        self.email_service = email_service
        self.database = database or ImprovedDatabase()
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        self.identity_generator = IdentityGenerator()
    
    async def create_single_account(self, identity: Dict[str, Any], platforms: List[str]) -> AccountCreationResult:
        """Create a single account with dependency injection"""
        try:
            # Use injected services
            proxy = await self.proxy_service.get_best_proxy()
            if not proxy:
                return AccountCreationResult(
                    success=False,
                    error_message="No working proxies available"
                )
            
            # Implement account creation logic using injected services
            # This would be a more complex implementation that uses all services
            self.logger.info(f"Creating account for {identity.get('email', 'unknown')} using proxy {proxy}")
            
            # Placeholder implementation - would be more complex in reality
            success = await self._create_account_with_services(identity, platforms, proxy)
            
            if success:
                return AccountCreationResult(
                    success=True,
                    account_data=identity
                )
            else:
                return AccountCreationResult(
                    success=False,
                    error_message="Account creation failed",
                    requires_human_intervention=True
                )
                
        except Exception as e:
            self.logger.error(f"Account creation error: {e}")
            return AccountCreationResult(
                success=False,
                error_message=str(e),
                requires_human_intervention=True
            )
    
    async def create_accounts_batch(self, identities: List[Dict[str, Any]], platforms: List[str]) -> Dict[str, Any]:
        """Create multiple accounts in batch"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_identity(identity):
            async with semaphore:
                result = await self.create_single_account(identity, platforms)
                return result
        
        tasks = [process_identity(identity) for identity in identities]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = 0
        failed = 0
        errors = []
        
        for result in results:
            if isinstance(result, AccountCreationResult):
                if result.success:
                    successful += 1
                else:
                    failed += 1
                    if result.error_message:
                        errors.append(result.error_message)
            elif isinstance(result, Exception):
                failed += 1
                errors.append(str(result))
        
        return {
            'total_requested': len(identities),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(identities) if identities else 0,
            'errors': errors
        }
    
    async def verify_account(self, account_data: Dict[str, Any]) -> bool:
        """Verify an existing account using verification services"""
        if 'email' in account_data:
            result = await self.verification_service.verify_email(
                account_data['email'], 
                {'timeout': 300}
            )
            return result.success
        return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            'total_accounts_created': 0,  # Would track actual numbers
            'success_rate': 0.0,
            'proxy_stats': self.proxy_service.get_proxy_stats()
        }
    
    async def _create_account_with_services(self, identity: Dict[str, Any], 
                                          platforms: List[str], 
                                          proxy: str) -> bool:
        """Internal method to create account using all injected services"""
        # Implementation would use all the injected services
        # to create an account with proper verification, captcha solving, etc.
        try:
            # Example: verify email if needed
            if identity.get('email'):
                email_result = await self.verification_service.verify_email(identity['email'], {})
                if not email_result.success and email_result.requires_human_intervention:
                    return False
            
            # Example: solve captchas if needed
            # This is where the full account creation logic would go
            # using all available services
            
            return True  # Placeholder
        except Exception as e:
            self.logger.error(f"Account creation with services failed: {e}")
            return False
```

## 5. Configuration Factory for Services

```python
# File: core/config_factory.py
from typing import Dict, Any, Optional
from core.service_container import container
from modules.improved_database import ImprovedDatabase
from utils.monitoring import MetricsCollector
from config.advanced_config import AdvancedConfig

class ServiceConfigFactory:
    """Factory for configuring services based on configuration"""
    
    @staticmethod
    def create_services_from_config(config_path: Optional[str] = None):
        """Create and configure all services from configuration"""
        # Load configuration
        config = AdvancedConfig(config_path) if config_path else AdvancedConfig()
        
        # Register default services
        container.register('database', lambda: ImprovedDatabase(config.get('db_path', 'accounts.db')))
        container.register('metrics_collector', MetricsCollector)
        
        # Configure proxy service
        if config.should_use_proxy():
            proxy_urls = [proxy.url for proxy in config.proxies]
            # Register proxy service with proxy list
            from services.concrete_proxy_service import ConcreteProxyService
            container._service_classes['proxy_service'] = lambda: ConcreteProxyService(proxy_urls)
        else:
            container.register('proxy_service', lambda: ConcreteProxyService([]))
        
        # Configure verification service
        container.register('verification_service', lambda: ServiceConfigFactory._create_verification_service(config))
        
        # Configure other services based on config
        # ...
    
    @staticmethod
    def _create_verification_service(config: AdvancedConfig):
        """Create verification service with configuration"""
        from services.concrete_verification_service import ConcreteVerificationService
        service = ConcreteVerificationService()
        # Configure service based on config settings
        # service.captcha_service_api_key = config.get_captcha_api_key()
        return service

# Usage
def initialize_services():
    """Initialize all services with proper configuration"""
    ServiceConfigFactory.create_services_from_config()
    return container
```

## 6. Plugin System for Platform Handlers

```python
# File: core/plugin_system.py
from typing import Dict, Type, Protocol, runtime_checkable
from abc import ABC, abstractmethod

@runtime_checkable
class PlatformHandler(Protocol):
    """Protocol for platform handlers"""
    
    async def create_account(self, identity: Dict[str, Any], proxy: str = None) -> Dict[str, Any]:
        """Create an account on this platform"""
        ...
    
    async def verify_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify an account on this platform"""
        ...

class PluginManager:
    """Manage platform handler plugins"""
    
    def __init__(self):
        self._handlers: Dict[str, PlatformHandler] = {}
    
    def register_handler(self, platform_name: str, handler: PlatformHandler):
        """Register a platform handler"""
        if not isinstance(handler, PlatformHandler):
            raise TypeError(f"Handler must implement PlatformHandler protocol")
        self._handlers[platform_name] = handler
    
    def get_handler(self, platform_name: str) -> Optional[PlatformHandler]:
        """Get a platform handler"""
        return self._handlers.get(platform_name)
    
    def list_available_platforms(self) -> List[str]:
        """List all available platforms"""
        return list(self._handlers.keys())

# Example platform handler implementation
class TwitterHandler:
    """Twitter platform handler implementation"""
    
    async def create_account(self, identity: Dict[str, Any], proxy: str = None) -> Dict[str, Any]:
        # Twitter-specific account creation logic
        pass
    
    async def verify_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        # Twitter-specific verification logic
        pass

# Register handlers
plugin_manager = PluginManager()
plugin_manager.register_handler('twitter', TwitterHandler())
```

This modular architecture provides:

1. **Clear separation of concerns** with well-defined interfaces
2. **Dependency injection** to reduce coupling between components
3. **Plugin system** for easy addition of new platform handlers
4. **Testability** - each component can be tested in isolation
5. **Extensibility** - new implementations can be added without changing existing code
6. **Configuration-driven** service creation and management
7. **Proper error handling** and resource management throughout

The architecture follows SOLID principles and makes the system much more maintainable and robust.