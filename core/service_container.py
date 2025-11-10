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
        
        # Register proxy service (with empty proxy list by default)
        self.register('proxy_service', lambda: ConcreteProxyService([]), singleton=True)
    
    def build_account_manager(self):
        """Build account manager with all dependencies injected"""
        # This would build the account manager with all dependencies
        from modules.di_account_manager import DIEnabledAccountManager
        verification_service = self.get('verification_service')
        proxy_service = self.get('proxy_service')
        
        # Create the account manager with dependencies
        from modules.improved_database import ImprovedDatabase
        from utils.monitoring import MetricsCollector
        return DIEnabledAccountManager(
            verification_service=verification_service,
            proxy_service=proxy_service,
            captcha_service=None,  # Would need to create or get this
            email_service=None,    # Would need to create or get this
            database=ImprovedDatabase(),
            metrics_collector=MetricsCollector()
        )

# Global service container instance
container = ServiceContainer()