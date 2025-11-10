from interfaces.proxy_service import AbstractProxyService, ProxyStats
from utils.proxy_manager import ImprovedProxyManager
import asyncio
import requests
import time
import logging

class ConcreteProxyService(AbstractProxyService):
    """Concrete implementation of proxy service"""
    
    def __init__(self, proxies: list = None):
        self.logger = logging.getLogger(__name__)
        self.proxies = proxies or []
        self.proxy_manager = ImprovedProxyManager(self.proxies)
    
    async def get_best_proxy(self) -> str:
        """Get the best available proxy based on performance metrics"""
        return await self.proxy_manager.get_best_proxy()
    
    async def test_proxy(self, proxy: str) -> tuple:
        """Test if a proxy is working and measure response time"""
        start_time = time.time()
        
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxy_dict,
                timeout=10
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return True, response_time
            else:
                return False, response_time
                
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.debug(f"Proxy {proxy} test failed: {e}")
            return False, response_time
    
    def record_success(self, proxy: str, response_time: float):
        """Record successful use of a proxy"""
        self.proxy_manager.record_success(proxy, response_time)
    
    def record_failure(self, proxy: str, response_time: float = None):
        """Record failed use of a proxy"""
        self.proxy_manager.record_failure(proxy, response_time)
    
    def get_proxy_stats(self) -> dict:
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