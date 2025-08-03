import asyncio
import time
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import threading

from modules.improved_database import ImprovedDatabase
from modules.improved_email_registration import ImprovedEmailRegistration
from modules.account_orchestrator import AccountOrchestrator
from utils.proxy_manager import ImprovedProxyManager
from utils.monitoring import MetricsCollector, PerformanceMonitor, AlertManager
from utils.identity_generator import IdentityGenerator
from utils.stealth_browser import StealthBrowserAutomation
from modules.advanced_verification_solver import AdvancedVerificationSolver
from utils.notifier import Notifier

@dataclass
class BatchResult:
    """Result of batch account creation"""
    total_requested: int
    successful_accounts: int
    failed_accounts: int
    success_rate: float
    total_duration: float
    avg_duration_per_account: float
    errors: List[Dict[str, Any]]
    successful_ecosystems: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AccountCreationTask:
    """Individual account creation task"""
    task_id: str
    identity: Dict[str, Any]
    platforms: List[str]
    priority: int = 1
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ImprovedAccountManager:
    """Enhanced account manager with comprehensive features"""
    
    def __init__(self, proxy_list: List[str] = None, max_workers: int = 5, 
                 db_path: str = "accounts.db"):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self._shutdown_event = threading.Event()
        
        # Initialize core components
        self.database = ImprovedDatabase(db_path)
        self.metrics_collector = MetricsCollector()
        self.performance_monitor = PerformanceMonitor(self.metrics_collector)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.notifier = Notifier()
        
        # Initialize proxy manager if proxies provided
        self.proxy_manager = None
        if proxy_list:
            self.proxy_manager = ImprovedProxyManager(proxy_list)
        
        # Initialize specialized components
        self.identity_generator = IdentityGenerator()
        self.browser_automation = StealthBrowserAutomation()
        self.verification_solver = AdvancedVerificationSolver()
        
        # Initialize registration handlers
        self.email_registration = ImprovedEmailRegistration(
            self.proxy_manager, 
            self.metrics_collector
        )
        self.account_orchestrator = AccountOrchestrator(
            self.proxy_manager,
            self.metrics_collector
        )
        
        # Task management
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        self.completed_tasks = {}
        
        # Performance tracking
        self.session_stats = {
            'start_time': datetime.now(),
            'accounts_created': 0,
            'accounts_failed': 0,
            'total_duration': 0.0,
            'platform_stats': {},
            'error_counts': {}
        }
        
        # Rate limiting
        self.rate_limiter = {
            'requests_per_minute': 10,
            'accounts_per_hour': 20,
            'last_request_times': [],
            'hourly_account_count': 0,
            'hour_start': datetime.now()
        }
    
    async def create_accounts_batch(self, identities: List[Dict[str, Any]], 
                                  platforms: List[str], 
                                  strategy: str = 'ecosystem') -> BatchResult:
        """Create multiple accounts efficiently with comprehensive management"""
        
        start_time = time.time()
        self.logger.info(f"Starting batch creation: {len(identities)} accounts across {platforms}")
        
        # Validate inputs
        if not identities:
            raise ValueError("No identities provided")
        if not platforms:
            raise ValueError("No platforms specified")
        
        # Initialize batch tracking
        batch_id = f"batch_{int(time.time())}_{random.randint(1000, 9999)}"
        results = []
        errors = []
        successful_ecosystems = []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_single_identity(identity_data, index):
            """Process a single identity with comprehensive error handling"""
            async with semaphore:
                task_id = f"{batch_id}_{index}"
                
                try:
                    # Check rate limiting
                    await self._enforce_rate_limiting()
                    
                    # Create account ecosystem
                    result = await self._create_single_account_ecosystem(
                        identity_data, platforms, task_id, strategy
                    )
                    
                    # Update session statistics
                    self._update_session_stats(result, platforms)
                    
                    return result
                    
                except Exception as e:
                    error_info = {
                        'task_id': task_id,
                        'identity': identity_data.get('email', 'unknown'),
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    errors.append(error_info)
                    self.logger.error(f"Task {task_id} failed: {e}")
                    return {'success': False, 'error': str(e), 'task_id': task_id}
        
        # Process all identities concurrently
        self.logger.info(f"Processing {len(identities)} identities with {self.max_workers} workers")
        
        tasks = [
            process_single_identity(identity, i) 
            for i, identity in enumerate(identities)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_count = 0
        failed_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed_count += 1
                errors.append({
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                })
            elif isinstance(result, dict):
                if result.get('success', False):
                    successful_count += 1
                    if 'ecosystem' in result:
                        successful_ecosystems.append(result['ecosystem'])
                else:
                    failed_count += 1
                    if 'error' in result:
                        errors.append({
                            'task_id': result.get('task_id', 'unknown'),
                            'error': result['error'],
                            'timestamp': datetime.now().isoformat()
                        })
        
        # Calculate final statistics
        total_duration = time.time() - start_time
        success_rate = successful_count / len(identities) if identities else 0
        avg_duration = total_duration / len(identities) if identities else 0
        
        batch_result = BatchResult(
            total_requested=len(identities),
            successful_accounts=successful_count,
            failed_accounts=failed_count,
            success_rate=success_rate,
            total_duration=total_duration,
            avg_duration_per_account=avg_duration,
            errors=errors,
            successful_ecosystems=successful_ecosystems
        )
        
        # Log batch completion
        self.logger.info(f"Batch {batch_id} completed: {successful_count}/{len(identities)} successful "
                        f"({success_rate:.2%}) in {total_duration:.1f}s")
        
        # Send notifications if needed
        if success_rate < 0.5:  # Less than 50% success rate
            self.notifier.low_success_rate_alert(batch_id, success_rate, errors[:5])
        
        # Check for alerts
        self.alert_manager.check_alerts()
        
        return batch_result
    
    async def _create_single_account_ecosystem(self, identity: Dict[str, Any], 
                                             platforms: List[str], 
                                             task_id: str,
                                             strategy: str) -> Dict[str, Any]:
        """Create a single account ecosystem with comprehensive tracking"""
        
        start_time = time.time()
        
        try:
            # Generate identity seed for consistency
            identity_seed = f"{task_id}_{identity.get('email', 'unknown')}"
            
            # Create account ecosystem using orchestrator
            ecosystem = await self.account_orchestrator.create_account_ecosystem(
                identity_seed=identity_seed,
                platforms=platforms,
                strategy=strategy
            )
            
            # Log operation
            duration = time.time() - start_time
            success = ecosystem.success_rate > 0.5
            
            self.database.log_operation(
                operation_type='ecosystem_creation',
                platform=','.join(platforms),
                success=success,
                duration=duration,
                account_email=ecosystem.primary_account.email,
                metadata={
                    'task_id': task_id,
                    'strategy': strategy,
                    'platforms': platforms,
                    'success_rate': ecosystem.success_rate,
                    'total_accounts': len(ecosystem.linked_accounts) + 1
                }
            )
            
            # Save ecosystem to database
            ecosystem_data = ecosystem.to_dict()
            self.database.save_account_ecosystem(ecosystem_data)
            
            return {
                'success': success,
                'task_id': task_id,
                'ecosystem': ecosystem_data,
                'duration': duration,
                'primary_email': ecosystem.primary_account.email,
                'success_rate': ecosystem.success_rate
            }
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log failure
            self.database.log_operation(
                operation_type='ecosystem_creation',
                platform=','.join(platforms),
                success=False,
                error_message=str(e),
                duration=duration,
                metadata={
                    'task_id': task_id,
                    'strategy': strategy,
                    'platforms': platforms
                }
            )
            
            raise e
    
    async def _enforce_rate_limiting(self):
        """Enforce rate limiting to prevent detection and overload"""
        current_time = datetime.now()
        
        # Check hourly limit
        if current_time.hour != self.rate_limiter['hour_start'].hour:
            self.rate_limiter['hourly_account_count'] = 0
            self.rate_limiter['hour_start'] = current_time
        
        if self.rate_limiter['hourly_account_count'] >= self.rate_limiter['accounts_per_hour']:
            wait_time = 3600 - (current_time.minute * 60 + current_time.second)
            self.logger.warning(f"Hourly rate limit reached, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            self.rate_limiter['hourly_account_count'] = 0
            self.rate_limiter['hour_start'] = datetime.now()
        
        # Check per-minute limit
        minute_ago = current_time - timedelta(minutes=1)
        self.rate_limiter['last_request_times'] = [
            t for t in self.rate_limiter['last_request_times'] 
            if t > minute_ago
        ]
        
        if len(self.rate_limiter['last_request_times']) >= self.rate_limiter['requests_per_minute']:
            wait_time = 60 - (current_time.second)
            self.logger.info(f"Per-minute rate limit reached, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
        
        # Record this request
        self.rate_limiter['last_request_times'].append(current_time)
        self.rate_limiter['hourly_account_count'] += 1
        
        # Add random delay to appear more human
        human_delay = random.uniform(2, 8)
        await asyncio.sleep(human_delay)
    
    def _update_session_stats(self, result: Dict[str, Any], platforms: List[str]):
        """Update session statistics"""
        if result.get('success', False):
            self.session_stats['accounts_created'] += 1
        else:
            self.session_stats['accounts_failed'] += 1
        
        self.session_stats['total_duration'] += result.get('duration', 0)
        
        # Update platform stats
        for platform in platforms:
            if platform not in self.session_stats['platform_stats']:
                self.session_stats['platform_stats'][platform] = {
                    'attempts': 0, 'successes': 0
                }
            
            self.session_stats['platform_stats'][platform]['attempts'] += 1
            if result.get('success', False):
                self.session_stats['platform_stats'][platform]['successes'] += 1
        
        # Update error counts
        if 'error' in result:
            error_type = result['error'][:50]  # Truncate long errors
            self.session_stats['error_counts'][error_type] = \
                self.session_stats['error_counts'].get(error_type, 0) + 1
    
    async def create_single_account(self, identity: Dict[str, Any], 
                                  platforms: List[str]) -> Dict[str, Any]:
        """Create a single account with comprehensive handling"""
        
        task_id = f"single_{int(time.time())}_{random.randint(1000, 9999)}"
        
        try:
            await self._enforce_rate_limiting()
            
            result = await self._create_single_account_ecosystem(
                identity, platforms, task_id, 'ecosystem'
            )
            
            self._update_session_stats(result, platforms)
            return result
            
        except Exception as e:
            self.logger.error(f"Single account creation failed: {e}")
            return {'success': False, 'error': str(e), 'task_id': task_id}
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get current session statistics"""
        current_time = datetime.now()
        session_duration = (current_time - self.session_stats['start_time']).total_seconds()
        
        total_attempts = self.session_stats['accounts_created'] + self.session_stats['accounts_failed']
        success_rate = (self.session_stats['accounts_created'] / max(total_attempts, 1))
        
        # Calculate platform success rates
        platform_stats = {}
        for platform, stats in self.session_stats['platform_stats'].items():
            platform_stats[platform] = {
                **stats,
                'success_rate': stats['successes'] / max(stats['attempts'], 1)
            }
        
        return {
            'session_duration_seconds': session_duration,
            'total_attempts': total_attempts,
            'successful_accounts': self.session_stats['accounts_created'],
            'failed_accounts': self.session_stats['accounts_failed'],
            'success_rate': success_rate,
            'avg_duration_per_account': (
                self.session_stats['total_duration'] / max(total_attempts, 1)
            ),
            'accounts_per_hour': (
                self.session_stats['accounts_created'] / max(session_duration / 3600, 1)
            ),
            'platform_statistics': platform_stats,
            'top_errors': sorted(
                self.session_stats['error_counts'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        return {
            'database_stats': self.database.get_database_stats(),
            'success_stats_24h': self.database.get_success_statistics(hours=24),
            'success_stats_7d': self.database.get_success_statistics(hours=168),
            'proxy_stats': self.database.get_proxy_stats(limit=10)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        try:
            # Check database
            db_stats = self.database.get_database_stats()
            health_status['components']['database'] = {
                'status': 'healthy' if db_stats else 'unhealthy',
                'stats': db_stats
            }
            
            # Check proxy manager
            if self.proxy_manager:
                proxy_stats = await self.proxy_manager.get_proxy_stats()
                healthy_proxies = len([p for p in proxy_stats.values() 
                                     if p.get('success_rate', 0) > 0.5])
                health_status['components']['proxy_manager'] = {
                    'status': 'healthy' if healthy_proxies > 0 else 'degraded',
                    'healthy_proxies': healthy_proxies,
                    'total_proxies': len(proxy_stats)
                }
            
            # Check system resources
            system_health = self.performance_monitor.get_system_health()
            health_status['components']['system_resources'] = {
                'status': 'healthy' if system_health.cpu_usage < 80 and system_health.memory_usage < 80 else 'degraded',
                'cpu_usage': system_health.cpu_usage,
                'memory_usage': system_health.memory_usage,
                'disk_usage': system_health.disk_usage
            }
            
            # Check recent success rate
            recent_stats = self.database.get_success_statistics(hours=1)
            recent_success_rate = recent_stats.get('overall', {}).get('success_rate', 0)
            health_status['components']['recent_performance'] = {
                'status': 'healthy' if recent_success_rate > 0.5 else 'degraded',
                'success_rate': recent_success_rate,
                'total_attempts': recent_stats.get('overall', {}).get('total_attempts', 0)
            }
            
            # Determine overall status
            component_statuses = [comp['status'] for comp in health_status['components'].values()]
            if 'unhealthy' in component_statuses:
                health_status['overall_status'] = 'unhealthy'
            elif 'degraded' in component_statuses:
                health_status['overall_status'] = 'degraded'
            
        except Exception as e:
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """Optimize performance based on current statistics"""
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'optimizations_applied': []
        }
        
        try:
            # Get current statistics
            stats = self.database.get_success_statistics(hours=24)
            
            # Optimize proxy selection if available
            if self.proxy_manager:
                proxy_stats = stats.get('proxy_performance', [])
                
                # Blacklist poorly performing proxies
                for proxy_stat in proxy_stats:
                    if proxy_stat['success_rate'] < 0.3 and proxy_stat['total_uses'] > 5:
                        await self.proxy_manager.blacklist_proxy(
                            proxy_stat['proxy'], 
                            "Low success rate"
                        )
                        optimization_results['optimizations_applied'].append(
                            f"Blacklisted proxy {proxy_stat['proxy']} (success rate: {proxy_stat['success_rate']:.2%})"
                        )
            
            # Adjust rate limiting based on success rates
            overall_success_rate = stats.get('overall', {}).get('success_rate', 0)
            
            if overall_success_rate < 0.5:
                # Reduce rate limits to improve success rate
                self.rate_limiter['requests_per_minute'] = max(5, self.rate_limiter['requests_per_minute'] - 2)
                self.rate_limiter['accounts_per_hour'] = max(10, self.rate_limiter['accounts_per_hour'] - 5)
                optimization_results['optimizations_applied'].append(
                    f"Reduced rate limits due to low success rate ({overall_success_rate:.2%})"
                )
            elif overall_success_rate > 0.8:
                # Increase rate limits if performing well
                self.rate_limiter['requests_per_minute'] = min(20, self.rate_limiter['requests_per_minute'] + 1)
                self.rate_limiter['accounts_per_hour'] = min(50, self.rate_limiter['accounts_per_hour'] + 2)
                optimization_results['optimizations_applied'].append(
                    f"Increased rate limits due to high success rate ({overall_success_rate:.2%})"
                )
            
            # Clean up old logs to improve database performance
            cleaned_logs = self.database.cleanup_old_logs(days=7)
            if cleaned_logs > 0:
                optimization_results['optimizations_applied'].append(
                    f"Cleaned up {cleaned_logs} old log entries"
                )
            
        except Exception as e:
            optimization_results['error'] = str(e)
        
        return optimization_results
    
    def export_accounts(self, format: str = 'json', platform: str = None, 
                       limit: int = None) -> str:
        """Export accounts in various formats"""
        return self.database.export_accounts(format, platform)
    
    def shutdown(self):
        """Graceful shutdown of the account manager"""
        self.logger.info("Shutting down account manager...")
        
        self._shutdown_event.set()
        
        # Close database connections
        self.database.close()
        
        # Close proxy manager if exists
        if self.proxy_manager:
            # Proxy manager doesn't have explicit close method in current implementation
            pass
        
        self.logger.info("Account manager shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()