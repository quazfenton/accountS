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
            if self.proxy_service is not None:
                proxy = await self.proxy_service.get_best_proxy()
            else:
                proxy = None
                
            if proxy is None and len(self.database.get_proxy_stats()) > 0:
                # Fallback to database proxy if service not available
                proxy_stats = self.database.get_proxy_stats(limit=1)
                if proxy_stats:
                    proxy = proxy_stats[0].get('proxy', None)
            
            # Implement account creation logic using injected services
            # This would be a more complex implementation that uses all services
            self.logger.info(f"Creating account for {identity.get('email', 'unknown')}")
            
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
        if self.email_service and 'email' in account_data:
            result = await self.email_service.get_verification_code(account_data['email'])
            return result.success
        return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        proxy_stats = {}
        if self.proxy_service:
            proxy_stats = self.proxy_service.get_proxy_stats()
        
        return {
            'total_accounts_created': 0,  # Would track actual numbers
            'success_rate': 0.0,
            'proxy_stats': proxy_stats
        }
    
    async def _create_account_with_services(self, identity: Dict[str, Any], 
                                          platforms: List[str], 
                                          proxy: str) -> bool:
        """Internal method to create account using all injected services"""
        # Implementation would use all the injected services
        # to create an account with proper verification, captcha solving, etc.
        try:
            # Example: verify email if needed
            if self.email_service and identity.get('email'):
                email_result = await self.email_service.get_verification_code(identity['email'])
                if not email_result.success and hasattr(email_result, 'requires_human_intervention'):
                    return False
            
            # Example: solve captchas if needed
            # This is where the full account creation logic would go
            # using all available services
            
            return True  # Placeholder
        except Exception as e:
            self.logger.error(f"Account creation with services failed: {e}")
            return False