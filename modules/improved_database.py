import sqlite3
import json
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import hashlib
import os

@dataclass
class AccountRecord:
    """Structured account record"""
    id: Optional[int] = None
    email: str = ""
    password: str = ""
    platform: str = ""
    username: str = ""
    proxy_used: str = ""
    success_rate: float = 0.0
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    status: str = "active"
    profile_data: Dict[str, Any] = None
    verification_status: str = "unverified"
    ecosystem_id: Optional[str] = None
    linked_accounts: List[str] = None
    
    def __post_init__(self):
        if self.profile_data is None:
            self.profile_data = {}
        if self.linked_accounts is None:
            self.linked_accounts = []
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ProxyStats:
    """Proxy statistics record"""
    proxy: str
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    blacklisted: bool = False
    avg_response_time: float = 0.0
    total_usage_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / max(total, 1)

@dataclass
class OperationLog:
    """Operation log record"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    operation_type: str = ""
    platform: str = ""
    success: bool = False
    error_message: str = ""
    duration_seconds: float = 0.0
    proxy_used: str = ""
    account_email: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class ImprovedDatabase:
    """Enhanced database with comprehensive account management"""
    
    def __init__(self, db_path: str = "accounts.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._connection_pool = {}
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe database connection context manager"""
        thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id not in self._connection_pool:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
                conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
                self._connection_pool[thread_id] = conn
            
            yield self._connection_pool[thread_id]
    
    def init_database(self):
        """Initialize SQLite database with comprehensive schema"""
        try:
            with self.get_connection() as conn:
                # Main accounts table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        username TEXT,
                        proxy_used TEXT,
                        success_rate REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        profile_data TEXT,
                        verification_status TEXT DEFAULT 'unverified',
                        ecosystem_id TEXT,
                        linked_accounts TEXT,
                        password_hash TEXT,
                        recovery_info TEXT,
                        notes TEXT
                    )
                ''')
                
                # Account ecosystems table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS account_ecosystems (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ecosystem_id TEXT UNIQUE NOT NULL,
                        identity_seed TEXT NOT NULL,
                        creation_strategy TEXT,
                        primary_email TEXT,
                        total_accounts INTEGER DEFAULT 0,
                        successful_accounts INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 0.0,
                        total_creation_time REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        metadata TEXT
                    )
                ''')
                
                # Enhanced proxy statistics
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS proxy_stats (
                        proxy TEXT PRIMARY KEY,
                        success_count INTEGER DEFAULT 0,
                        failure_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP,
                        blacklisted BOOLEAN DEFAULT FALSE,
                        avg_response_time REAL DEFAULT 0.0,
                        total_usage_time REAL DEFAULT 0.0,
                        country TEXT,
                        provider TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                ''')
                
                # Comprehensive operation logs
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS operation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        operation_type TEXT NOT NULL,
                        platform TEXT,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        duration_seconds REAL DEFAULT 0.0,
                        proxy_used TEXT,
                        account_email TEXT,
                        metadata TEXT,
                        session_id TEXT,
                        user_agent TEXT,
                        ip_address TEXT
                    )
                ''')
                
                # Verification attempts tracking
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS verification_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        account_email TEXT NOT NULL,
                        verification_type TEXT NOT NULL,
                        platform TEXT,
                        success BOOLEAN,
                        attempts_count INTEGER DEFAULT 1,
                        last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        error_details TEXT,
                        service_used TEXT,
                        cost REAL DEFAULT 0.0,
                        FOREIGN KEY (account_email) REFERENCES accounts (email)
                    )
                ''')
                
                # Performance metrics
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metric_type TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        platform TEXT,
                        metadata TEXT
                    )
                ''')
                
                # Create indexes for better performance
                self._create_indexes(conn)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
            raise
    
    def _create_indexes(self, conn):
        """Create database indexes for better performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_accounts_email ON accounts(email)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)",
            "CREATE INDEX IF NOT EXISTS idx_accounts_ecosystem ON accounts(ecosystem_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON operation_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_platform ON operation_logs(platform)",
            "CREATE INDEX IF NOT EXISTS idx_logs_success ON operation_logs(success)",
            "CREATE INDEX IF NOT EXISTS idx_proxy_stats_proxy ON proxy_stats(proxy)",
            "CREATE INDEX IF NOT EXISTS idx_verification_email ON verification_attempts(account_email)",
            "CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"Index creation warning: {e}")
    
    def save_account(self, account_data: Dict[str, Any]) -> bool:
        """Save account with comprehensive data validation and error handling"""
        try:
            # Validate required fields
            required_fields = ['email', 'password', 'platform']
            for field in required_fields:
                if field not in account_data or not account_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create password hash for security
            password_hash = hashlib.sha256(account_data['password'].encode()).hexdigest()
            
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO accounts 
                    (email, password, platform, username, proxy_used, profile_data, 
                     verification_status, ecosystem_id, linked_accounts, password_hash, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_data['email'],
                    account_data['password'],
                    account_data.get('platform', 'unknown'),
                    account_data.get('username', ''),
                    account_data.get('proxy', ''),
                    json.dumps(account_data.get('profile', {})),
                    account_data.get('verification_status', 'unverified'),
                    account_data.get('ecosystem_id', ''),
                    json.dumps(account_data.get('linked_accounts', [])),
                    password_hash,
                    account_data.get('notes', '')
                ))
                conn.commit()
                
            self.logger.info(f"Account saved: {account_data['email']} ({account_data['platform']})")
            return True
            
        except Exception as e:
            self.logger.error(f"Database save error: {e}")
            return False
    
    def save_account_ecosystem(self, ecosystem_data: Dict[str, Any]) -> bool:
        """Save complete account ecosystem"""
        try:
            ecosystem_id = ecosystem_data.get('identity_seed', '') or f"eco_{int(datetime.now().timestamp())}"
            
            with self.get_connection() as conn:
                # Save ecosystem metadata
                conn.execute('''
                    INSERT OR REPLACE INTO account_ecosystems
                    (ecosystem_id, identity_seed, creation_strategy, primary_email,
                     total_accounts, successful_accounts, success_rate, total_creation_time, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ecosystem_id,
                    ecosystem_data.get('identity_seed', ''),
                    ecosystem_data.get('creation_strategy', ''),
                    ecosystem_data.get('primary_account', {}).get('email', ''),
                    len(ecosystem_data.get('linked_accounts', [])) + 1,
                    len([acc for acc in ecosystem_data.get('linked_accounts', []) 
                         if acc.get('status') in ['created', 'verified']]) + 
                    (1 if ecosystem_data.get('primary_account', {}).get('status') in ['created', 'verified'] else 0),
                    ecosystem_data.get('success_rate', 0.0),
                    ecosystem_data.get('total_creation_time', 0.0),
                    json.dumps(ecosystem_data)
                ))
                
                # Save primary account
                primary_account = ecosystem_data.get('primary_account', {})
                if primary_account:
                    primary_account['ecosystem_id'] = ecosystem_id
                    self.save_account(primary_account)
                
                # Save linked accounts
                for account in ecosystem_data.get('linked_accounts', []):
                    account['ecosystem_id'] = ecosystem_id
                    self.save_account(account)
                
                conn.commit()
                
            self.logger.info(f"Account ecosystem saved: {ecosystem_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ecosystem save error: {e}")
            return False
    
    def get_accounts(self, platform: str = None, status: str = "active", 
                    ecosystem_id: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve accounts with flexible filtering"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM accounts WHERE 1=1"
                params = []
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                if status:
                    query += " AND status = ?"
                    params.append(status)
                
                if ecosystem_id:
                    query += " AND ecosystem_id = ?"
                    params.append(ecosystem_id)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                accounts = []
                for row in rows:
                    account = dict(row)
                    # Parse JSON fields
                    if account['profile_data']:
                        account['profile_data'] = json.loads(account['profile_data'])
                    if account['linked_accounts']:
                        account['linked_accounts'] = json.loads(account['linked_accounts'])
                    accounts.append(account)
                
                return accounts
                
        except Exception as e:
            self.logger.error(f"Error retrieving accounts: {e}")
            return []
    
    def get_success_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive success statistics"""
        try:
            with self.get_connection() as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                # Overall statistics
                overall_stats = conn.execute('''
                    SELECT 
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                        AVG(duration_seconds) as avg_duration,
                        MIN(duration_seconds) as min_duration,
                        MAX(duration_seconds) as max_duration
                    FROM operation_logs
                    WHERE timestamp > ?
                ''', (cutoff_time,)).fetchone()
                
                # Platform-specific statistics
                platform_stats = conn.execute('''
                    SELECT 
                        platform,
                        COUNT(*) as attempts,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                        AVG(duration_seconds) as avg_duration,
                        COUNT(DISTINCT proxy_used) as unique_proxies
                    FROM operation_logs
                    WHERE timestamp > ? AND platform IS NOT NULL
                    GROUP BY platform
                    ORDER BY attempts DESC
                ''', (cutoff_time,)).fetchall()
                
                # Error analysis
                error_stats = conn.execute('''
                    SELECT 
                        error_message,
                        COUNT(*) as count,
                        platform
                    FROM operation_logs
                    WHERE timestamp > ? AND success = 0 AND error_message IS NOT NULL
                    GROUP BY error_message, platform
                    ORDER BY count DESC
                    LIMIT 10
                ''', (cutoff_time,)).fetchall()
                
                # Proxy performance
                proxy_stats = conn.execute('''
                    SELECT 
                        proxy_used,
                        COUNT(*) as total_uses,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                        AVG(duration_seconds) as avg_duration
                    FROM operation_logs
                    WHERE timestamp > ? AND proxy_used IS NOT NULL AND proxy_used != ''
                    GROUP BY proxy_used
                    ORDER BY total_uses DESC
                    LIMIT 10
                ''', (cutoff_time,)).fetchall()
                
                # Hourly breakdown
                hourly_stats = conn.execute('''
                    SELECT 
                        strftime('%H', timestamp) as hour,
                        COUNT(*) as attempts,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
                    FROM operation_logs
                    WHERE timestamp > ?
                    GROUP BY strftime('%H', timestamp)
                    ORDER BY hour
                ''', (cutoff_time,)).fetchall()
                
                return {
                    'time_period_hours': hours,
                    'overall': {
                        'total_attempts': overall_stats['total_attempts'] or 0,
                        'successes': overall_stats['successes'] or 0,
                        'success_rate': (overall_stats['successes'] or 0) / max(overall_stats['total_attempts'] or 1, 1),
                        'avg_duration': overall_stats['avg_duration'] or 0,
                        'min_duration': overall_stats['min_duration'] or 0,
                        'max_duration': overall_stats['max_duration'] or 0
                    },
                    'by_platform': [
                        {
                            'platform': row['platform'],
                            'attempts': row['attempts'],
                            'successes': row['successes'],
                            'success_rate': row['successes'] / max(row['attempts'], 1),
                            'avg_duration': row['avg_duration'] or 0,
                            'unique_proxies': row['unique_proxies']
                        }
                        for row in platform_stats
                    ],
                    'top_errors': [
                        {
                            'error': row['error_message'],
                            'count': row['count'],
                            'platform': row['platform']
                        }
                        for row in error_stats
                    ],
                    'proxy_performance': [
                        {
                            'proxy': row['proxy_used'],
                            'total_uses': row['total_uses'],
                            'successes': row['successes'],
                            'success_rate': row['successes'] / max(row['total_uses'], 1),
                            'avg_duration': row['avg_duration'] or 0
                        }
                        for row in proxy_stats
                    ],
                    'hourly_breakdown': [
                        {
                            'hour': int(row['hour']),
                            'attempts': row['attempts'],
                            'successes': row['successes'],
                            'success_rate': row['successes'] / max(row['attempts'], 1)
                        }
                        for row in hourly_stats
                    ]
                }
                
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
    
    def log_operation(self, operation_type: str, platform: str, success: bool, 
                     error_message: str = "", duration: float = 0.0, 
                     proxy_used: str = "", account_email: str = "", 
                     metadata: Dict[str, Any] = None) -> bool:
        """Log operation with comprehensive details"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO operation_logs 
                    (operation_type, platform, success, error_message, duration_seconds,
                     proxy_used, account_email, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    operation_type,
                    platform,
                    success,
                    error_message,
                    duration,
                    proxy_used,
                    account_email,
                    json.dumps(metadata or {})
                ))
                conn.commit()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging operation: {e}")
            return False
    
    def update_proxy_stats(self, proxy: str, success: bool, response_time: float = 0.0) -> bool:
        """Update proxy statistics"""
        try:
            with self.get_connection() as conn:
                # Check if proxy exists
                existing = conn.execute(
                    "SELECT success_count, failure_count, avg_response_time, total_usage_time FROM proxy_stats WHERE proxy = ?",
                    (proxy,)
                ).fetchone()
                
                if existing:
                    # Update existing record
                    new_success = existing['success_count'] + (1 if success else 0)
                    new_failure = existing['failure_count'] + (0 if success else 1)
                    total_requests = new_success + new_failure
                    
                    # Update average response time
                    old_avg = existing['avg_response_time'] or 0
                    old_total_time = existing['total_usage_time'] or 0
                    new_total_time = old_total_time + response_time
                    new_avg = new_total_time / max(total_requests, 1)
                    
                    conn.execute('''
                        UPDATE proxy_stats 
                        SET success_count = ?, failure_count = ?, last_used = CURRENT_TIMESTAMP,
                            avg_response_time = ?, total_usage_time = ?
                        WHERE proxy = ?
                    ''', (new_success, new_failure, new_avg, new_total_time, proxy))
                else:
                    # Insert new record
                    conn.execute('''
                        INSERT INTO proxy_stats 
                        (proxy, success_count, failure_count, last_used, avg_response_time, total_usage_time)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                    ''', (proxy, 1 if success else 0, 0 if success else 1, response_time, response_time))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error updating proxy stats: {e}")
            return False
    
    def get_proxy_stats(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get proxy statistics"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT proxy, success_count, failure_count, last_used, blacklisted,
                           avg_response_time, total_usage_time,
                           (success_count * 1.0 / NULLIF(success_count + failure_count, 0)) as success_rate
                    FROM proxy_stats
                    ORDER BY (success_count + failure_count) DESC
                '''
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor = conn.execute(query)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error getting proxy stats: {e}")
            return []
    
    def blacklist_proxy(self, proxy: str, reason: str = "") -> bool:
        """Blacklist a proxy"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE proxy_stats 
                    SET blacklisted = TRUE, notes = ?
                    WHERE proxy = ?
                ''', (reason, proxy))
                
                # Also insert if doesn't exist
                conn.execute('''
                    INSERT OR IGNORE INTO proxy_stats (proxy, blacklisted, notes)
                    VALUES (?, TRUE, ?)
                ''', (proxy, reason))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error blacklisting proxy: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Clean up old operation logs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM operation_logs WHERE timestamp < ?",
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old log entries")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Error cleaning up logs: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # Table counts
                tables = ['accounts', 'account_ecosystems', 'proxy_stats', 'operation_logs', 'verification_attempts']
                for table in tables:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    stats[f"{table}_count"] = count
                
                # Database size
                stats['database_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
                
                # Recent activity
                recent_logs = conn.execute(
                    "SELECT COUNT(*) FROM operation_logs WHERE timestamp > datetime('now', '-24 hours')"
                ).fetchone()[0]
                stats['recent_activity_24h'] = recent_logs
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def export_accounts(self, format: str = 'json', platform: str = None) -> str:
        """Export accounts in various formats"""
        try:
            accounts = self.get_accounts(platform=platform)
            
            if format.lower() == 'json':
                return json.dumps(accounts, indent=2, default=str)
            elif format.lower() == 'csv':
                if not accounts:
                    return ""
                
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=accounts[0].keys())
                writer.writeheader()
                
                for account in accounts:
                    # Convert complex fields to strings
                    row = account.copy()
                    for key, value in row.items():
                        if isinstance(value, (dict, list)):
                            row[key] = json.dumps(value)
                    writer.writerow(row)
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting accounts: {e}")
            return ""
    
    def close(self):
        """Close all database connections"""
        with self._lock:
            for conn in self._connection_pool.values():
                try:
                    conn.close()
                except:
                    pass
            self._connection_pool.clear()
    
    def __del__(self):
        """Cleanup on destruction"""
        self.close()