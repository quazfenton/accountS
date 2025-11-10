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