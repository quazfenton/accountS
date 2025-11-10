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