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