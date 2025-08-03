import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import sqlite3
import os

@dataclass
class AccountCreationMetric:
    timestamp: datetime
    platform: str
    success: bool
    error_type: Optional[str] = None
    proxy_used: Optional[str] = None
    captcha_solved: bool = False
    verification_method: Optional[str] = None
    creation_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class SystemHealthMetric:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_threads: int
    proxy_health: Dict[str, Any]
    success_rate_1h: float
    success_rate_24h: float
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class MetricsCollector:
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self.metrics_buffer = deque(maxlen=1000)  # Keep last 1000 metrics in memory
        self.system_metrics_buffer = deque(maxlen=100)  # Keep last 100 system metrics
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        
        # Start background thread for periodic tasks
        self.background_thread = threading.Thread(target=self._background_tasks, daemon=True)
        self.background_thread.start()
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS account_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_type TEXT,
                    proxy_used TEXT,
                    captcha_solved BOOLEAN,
                    verification_method TEXT,
                    creation_time_seconds REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    active_threads INTEGER,
                    proxy_health TEXT,
                    success_rate_1h REAL,
                    success_rate_24h REAL
                )
            """)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_account_timestamp ON account_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_account_platform ON account_metrics(platform)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp)")
    
    def record_account_creation(self, metric: AccountCreationMetric):
        """Record an account creation attempt"""
        with self.lock:
            self.metrics_buffer.append(metric)
        
        # Persist to database
        self._persist_account_metric(metric)
    
    def record_system_health(self, metric: SystemHealthMetric):
        """Record system health metrics"""
        with self.lock:
            self.system_metrics_buffer.append(metric)
        
        # Persist to database
        self._persist_system_metric(metric)
    
    def _persist_account_metric(self, metric: AccountCreationMetric):
        """Persist account metric to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO account_metrics 
                    (timestamp, platform, success, error_type, proxy_used, 
                     captcha_solved, verification_method, creation_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.timestamp.isoformat(),
                    metric.platform,
                    metric.success,
                    metric.error_type,
                    metric.proxy_used,
                    metric.captcha_solved,
                    metric.verification_method,
                    metric.creation_time_seconds
                ))
        except Exception as e:
            self.logger.error(f"Failed to persist account metric: {e}")
    
    def _persist_system_metric(self, metric: SystemHealthMetric):
        """Persist system metric to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_metrics 
                    (timestamp, cpu_usage, memory_usage, disk_usage, 
                     active_threads, proxy_health, success_rate_1h, success_rate_24h)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metric.timestamp.isoformat(),
                    metric.cpu_usage,
                    metric.memory_usage,
                    metric.disk_usage,
                    metric.active_threads,
                    json.dumps(metric.proxy_health),
                    metric.success_rate_1h,
                    metric.success_rate_24h
                ))
        except Exception as e:
            self.logger.error(f"Failed to persist system metric: {e}")
    
    def get_success_rate(self, hours: int = 1, platform: str = None) -> float:
        """Get success rate for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT COUNT(*) as total, SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
                    FROM account_metrics 
                    WHERE timestamp > ?
                """
                params = [cutoff_time.isoformat()]
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                cursor = conn.execute(query, params)
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    return result[1] / result[0]
                return 0.0
        except Exception as e:
            self.logger.error(f"Failed to calculate success rate: {e}")
            return 0.0
    
    def get_platform_stats(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get statistics by platform for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        platform,
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                        AVG(creation_time_seconds) as avg_creation_time,
                        COUNT(DISTINCT proxy_used) as unique_proxies_used,
                        SUM(CASE WHEN captcha_solved THEN 1 ELSE 0 END) as captchas_solved
                    FROM account_metrics 
                    WHERE timestamp > ?
                    GROUP BY platform
                """, [cutoff_time.isoformat()])
                
                stats = {}
                for row in cursor.fetchall():
                    platform, total, successes, avg_time, unique_proxies, captchas = row
                    stats[platform] = {
                        'total_attempts': total,
                        'successes': successes,
                        'success_rate': successes / max(total, 1),
                        'avg_creation_time': avg_time or 0,
                        'unique_proxies_used': unique_proxies or 0,
                        'captchas_solved': captchas or 0
                    }
                
                return stats
        except Exception as e:
            self.logger.error(f"Failed to get platform stats: {e}")
            return {}
    
    def get_error_analysis(self, hours: int = 24) -> Dict[str, int]:
        """Get error analysis for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT error_type, COUNT(*) as count
                    FROM account_metrics 
                    WHERE timestamp > ? AND success = 0 AND error_type IS NOT NULL
                    GROUP BY error_type
                    ORDER BY count DESC
                """, [cutoff_time.isoformat()])
                
                return dict(cursor.fetchall())
        except Exception as e:
            self.logger.error(f"Failed to get error analysis: {e}")
            return {}
    
    def _background_tasks(self):
        """Background thread for periodic maintenance tasks"""
        while True:
            try:
                # Clean up old metrics (keep only last 30 days)
                cutoff_time = datetime.now() - timedelta(days=30)
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM account_metrics WHERE timestamp < ?", [cutoff_time.isoformat()])
                    conn.execute("DELETE FROM system_metrics WHERE timestamp < ?", [cutoff_time.isoformat()])
                
                # Sleep for 1 hour before next cleanup
                time.sleep(3600)
                
            except Exception as e:
                self.logger.error(f"Background task error: {e}")
                time.sleep(300)  # Sleep 5 minutes on error

class AlertManager:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        self.alert_thresholds = {
            'success_rate_1h': 0.5,  # Alert if success rate drops below 50% in 1 hour
            'success_rate_24h': 0.3,  # Alert if success rate drops below 30% in 24 hours
            'consecutive_failures': 5,  # Alert after 5 consecutive failures
            'proxy_failure_rate': 0.8,  # Alert if proxy failure rate exceeds 80%
        }
        self.last_alerts = {}  # Track last alert times to avoid spam
        self.alert_cooldown = 3600  # 1 hour cooldown between similar alerts
    
    def check_alerts(self):
        """Check for alert conditions and send notifications if needed"""
        current_time = datetime.now()
        
        # Check success rate alerts
        success_rate_1h = self.metrics_collector.get_success_rate(hours=1)
        success_rate_24h = self.metrics_collector.get_success_rate(hours=24)
        
        if success_rate_1h < self.alert_thresholds['success_rate_1h']:
            self._send_alert(
                'low_success_rate_1h',
                f"Success rate in last hour is {success_rate_1h:.2%} (threshold: {self.alert_thresholds['success_rate_1h']:.2%})"
            )
        
        if success_rate_24h < self.alert_thresholds['success_rate_24h']:
            self._send_alert(
                'low_success_rate_24h',
                f"Success rate in last 24 hours is {success_rate_24h:.2%} (threshold: {self.alert_thresholds['success_rate_24h']:.2%})"
            )
        
        # Check for consecutive failures
        consecutive_failures = self._count_consecutive_failures()
        if consecutive_failures >= self.alert_thresholds['consecutive_failures']:
            self._send_alert(
                'consecutive_failures',
                f"{consecutive_failures} consecutive failures detected"
            )
    
    def _count_consecutive_failures(self) -> int:
        """Count consecutive failures from the most recent attempts"""
        with self.metrics_collector.lock:
            consecutive = 0
            for metric in reversed(self.metrics_collector.metrics_buffer):
                if not metric.success:
                    consecutive += 1
                else:
                    break
            return consecutive
    
    def _send_alert(self, alert_type: str, message: str):
        """Send alert notification"""
        current_time = datetime.now()
        
        # Check cooldown
        if alert_type in self.last_alerts:
            time_since_last = (current_time - self.last_alerts[alert_type]).total_seconds()
            if time_since_last < self.alert_cooldown:
                return  # Skip alert due to cooldown
        
        # Send alert
        self.logger.critical(f"ALERT [{alert_type}]: {message}")
        
        # Try to send system notification
        try:
            from utils.notifier import Notifier
            notifier = Notifier()
            notifier.send_alert(f"Account Creation System Alert: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send system notification: {e}")
        
        # Update last alert time
        self.last_alerts[alert_type] = current_time

class PerformanceMonitor:
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
    
    def get_system_health(self) -> SystemHealthMetric:
        """Get current system health metrics"""
        try:
            import psutil
            
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get thread count
            active_threads = threading.active_count()
            
            # Calculate success rates
            success_rate_1h = self.metrics_collector.get_success_rate(hours=1)
            success_rate_24h = self.metrics_collector.get_success_rate(hours=24)
            
            return SystemHealthMetric(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                active_threads=active_threads,
                proxy_health={},  # This would be populated by proxy manager
                success_rate_1h=success_rate_1h,
                success_rate_24h=success_rate_24h
            )
            
        except ImportError:
            self.logger.warning("psutil not available, using basic system metrics")
            return SystemHealthMetric(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                active_threads=threading.active_count(),
                proxy_health={},
                success_rate_1h=self.metrics_collector.get_success_rate(hours=1),
                success_rate_24h=self.metrics_collector.get_success_rate(hours=24)
            )
    
    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        platform_stats = self.metrics_collector.get_platform_stats(hours)
        error_analysis = self.metrics_collector.get_error_analysis(hours)
        system_health = self.get_system_health()
        
        return {
            'report_generated': datetime.now().isoformat(),
            'time_period_hours': hours,
            'overall_success_rate': self.metrics_collector.get_success_rate(hours),
            'platform_statistics': platform_stats,
            'error_analysis': error_analysis,
            'system_health': system_health.to_dict(),
            'recommendations': self._generate_recommendations(platform_stats, error_analysis)
        }
    
    def _generate_recommendations(self, platform_stats: Dict, error_analysis: Dict) -> List[str]:
        """Generate recommendations based on performance data"""
        recommendations = []
        
        # Check for low success rates
        for platform, stats in platform_stats.items():
            if stats['success_rate'] < 0.5:
                recommendations.append(f"Consider reviewing {platform} registration process - success rate is {stats['success_rate']:.2%}")
        
        # Check for common errors
        if error_analysis:
            most_common_error = max(error_analysis.items(), key=lambda x: x[1])
            if most_common_error[1] > 5:  # More than 5 occurrences
                recommendations.append(f"Address '{most_common_error[0]}' error - occurred {most_common_error[1]} times")
        
        # Check for proxy issues
        total_attempts = sum(stats['total_attempts'] for stats in platform_stats.values())
        if total_attempts > 0:
            unique_proxies = sum(stats['unique_proxies_used'] for stats in platform_stats.values())
            if unique_proxies < total_attempts * 0.1:  # Less than 10% proxy diversity
                recommendations.append("Consider adding more proxies for better IP diversity")
        
        return recommendations