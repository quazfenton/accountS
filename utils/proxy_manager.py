import time
import random
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

@dataclass
class ProxyStats:
    successes: int = 0
    failures: int = 0
    last_used: Optional[datetime] = None
    response_times: List[float] = field(default_factory=list)
    consecutive_failures: int = 0
    blacklisted_until: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        total = self.successes + self.failures
        return self.successes / max(total, 1)
    
    @property
    def average_response_time(self) -> float:
        return sum(self.response_times) / max(len(self.response_times), 1)
    
    @property
    def is_blacklisted(self) -> bool:
        if self.blacklisted_until is None:
            return False
        return datetime.now() < self.blacklisted_until

class ImprovedProxyManager:
    def __init__(self, proxies: List[str], test_url: str = "http://httpbin.org/ip"):
        self.proxies = proxies
        self.test_url = test_url
        self.stats: Dict[str, ProxyStats] = {proxy: ProxyStats() for proxy in proxies}
        self.logger = logging.getLogger(__name__)
        self.min_cooldown_minutes = 5
        self.max_consecutive_failures = 3
        self.blacklist_duration_hours = 1
        
    async def get_best_proxy(self, exclude_recent: bool = True) -> Optional[str]:
        """Get the best performing proxy based on multiple criteria"""
        available_proxies = self._get_available_proxies(exclude_recent)
        
        if not available_proxies:
            self.logger.warning("No available proxies found")
            return None
        
        # Score proxies based on multiple factors
        scored_proxies = []
        for proxy in available_proxies:
            score = self._calculate_proxy_score(proxy)
            scored_proxies.append((proxy, score))
        
        # Sort by score (higher is better)
        scored_proxies.sort(key=lambda x: x[1], reverse=True)
        
        # Add some randomness to avoid always using the same "best" proxy
        top_proxies = scored_proxies[:min(3, len(scored_proxies))]
        weights = [score for _, score in top_proxies]
        
        if sum(weights) > 0:
            selected_proxy = random.choices(
                [proxy for proxy, _ in top_proxies],
                weights=weights
            )[0]
        else:
            selected_proxy = random.choice([proxy for proxy, _ in top_proxies])
        
        self.stats[selected_proxy].last_used = datetime.now()
        return selected_proxy
    
    def _get_available_proxies(self, exclude_recent: bool) -> List[str]:
        """Get list of available proxies (not blacklisted, optionally not recently used)"""
        available = []
        now = datetime.now()
        
        for proxy in self.proxies:
            stats = self.stats[proxy]
            
            # Skip blacklisted proxies
            if stats.is_blacklisted:
                continue
            
            # Skip recently used proxies if requested
            if exclude_recent and stats.last_used:
                minutes_since_use = (now - stats.last_used).total_seconds() / 60
                if minutes_since_use < self.min_cooldown_minutes:
                    continue
            
            available.append(proxy)
        
        return available
    
    def _calculate_proxy_score(self, proxy: str) -> float:
        """Calculate a score for proxy selection (higher is better)"""
        stats = self.stats[proxy]
        
        # Base score from success rate
        success_score = stats.success_rate * 100
        
        # Penalty for consecutive failures
        failure_penalty = stats.consecutive_failures * 10
        
        # Bonus for faster response times (inverse of average time)
        speed_bonus = 0
        if stats.response_times:
            avg_time = stats.average_response_time
            speed_bonus = max(0, 10 - avg_time)  # Bonus decreases as response time increases
        
        # Penalty for recent usage (to encourage rotation)
        recency_penalty = 0
        if stats.last_used:
            minutes_since_use = (datetime.now() - stats.last_used).total_seconds() / 60
            if minutes_since_use < 30:  # Penalty for usage within 30 minutes
                recency_penalty = (30 - minutes_since_use) / 3
        
        total_score = success_score + speed_bonus - failure_penalty - recency_penalty
        return max(0, total_score)
    
    async def test_proxy(self, proxy: str, timeout: int = 10) -> Tuple[bool, float]:
        """Test if a proxy is working and measure response time"""
        start_time = time.time()
        
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            response = requests.get(
                self.test_url,
                proxies=proxy_dict,
                timeout=timeout
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
    
    async def test_all_proxies(self) -> Dict[str, Tuple[bool, float]]:
        """Test all proxies concurrently"""
        tasks = []
        for proxy in self.proxies:
            task = asyncio.create_task(self.test_proxy(proxy))
            tasks.append((proxy, task))
        
        results = {}
        for proxy, task in tasks:
            try:
                is_working, response_time = await task
                results[proxy] = (is_working, response_time)
            except Exception as e:
                self.logger.error(f"Error testing proxy {proxy}: {e}")
                results[proxy] = (False, float('inf'))
        
        return results
    
    def record_success(self, proxy: str, response_time: float = None):
        """Record a successful use of a proxy"""
        if proxy not in self.stats:
            return
        
        stats = self.stats[proxy]
        stats.successes += 1
        stats.consecutive_failures = 0
        
        if response_time is not None:
            stats.response_times.append(response_time)
            # Keep only last 10 response times
            if len(stats.response_times) > 10:
                stats.response_times.pop(0)
        
        # Remove from blacklist if it was blacklisted
        stats.blacklisted_until = None
        
        self.logger.debug(f"Proxy {proxy} success recorded. Success rate: {stats.success_rate:.2f}")
    
    def record_failure(self, proxy: str, response_time: float = None):
        """Record a failed use of a proxy"""
        if proxy not in self.stats:
            return
        
        stats = self.stats[proxy]
        stats.failures += 1
        stats.consecutive_failures += 1
        
        if response_time is not None:
            stats.response_times.append(response_time)
            if len(stats.response_times) > 10:
                stats.response_times.pop(0)
        
        # Blacklist proxy if too many consecutive failures
        if stats.consecutive_failures >= self.max_consecutive_failures:
            stats.blacklisted_until = datetime.now() + timedelta(hours=self.blacklist_duration_hours)
            self.logger.warning(f"Proxy {proxy} blacklisted until {stats.blacklisted_until}")
        
        self.logger.debug(f"Proxy {proxy} failure recorded. Success rate: {stats.success_rate:.2f}")
    
    def get_proxy_stats(self) -> Dict[str, Dict]:
        """Get statistics for all proxies"""
        stats_dict = {}
        for proxy, stats in self.stats.items():
            stats_dict[proxy] = {
                'success_rate': stats.success_rate,
                'total_uses': stats.successes + stats.failures,
                'avg_response_time': stats.average_response_time,
                'consecutive_failures': stats.consecutive_failures,
                'is_blacklisted': stats.is_blacklisted,
                'last_used': stats.last_used.isoformat() if stats.last_used else None
            }
        return stats_dict
    
    def reset_proxy_stats(self, proxy: str = None):
        """Reset statistics for a specific proxy or all proxies"""
        if proxy:
            if proxy in self.stats:
                self.stats[proxy] = ProxyStats()
        else:
            self.stats = {proxy: ProxyStats() for proxy in self.proxies}
    
    def remove_proxy(self, proxy: str):
        """Remove a proxy from the pool"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            del self.stats[proxy]
            self.logger.info(f"Proxy {proxy} removed from pool")
    
    def add_proxy(self, proxy: str):
        """Add a new proxy to the pool"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.stats[proxy] = ProxyStats()
            self.logger.info(f"Proxy {proxy} added to pool")
    
    async def health_check(self) -> Dict[str, any]:
        """Perform a health check on all proxies"""
        test_results = await self.test_all_proxies()
        
        working_proxies = sum(1 for is_working, _ in test_results.values() if is_working)
        total_proxies = len(self.proxies)
        
        health_report = {
            'total_proxies': total_proxies,
            'working_proxies': working_proxies,
            'health_percentage': (working_proxies / max(total_proxies, 1)) * 100,
            'proxy_details': {}
        }
        
        for proxy, (is_working, response_time) in test_results.items():
            stats = self.stats[proxy]
            health_report['proxy_details'][proxy] = {
                'is_working': is_working,
                'response_time': response_time,
                'success_rate': stats.success_rate,
                'is_blacklisted': stats.is_blacklisted
            }
        
        return health_report