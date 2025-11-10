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