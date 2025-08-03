DONE

project:    ./accountS

Next Steps:**

1.  **Implement `utils/model.py` as a placeholder for `FaceGenerator`**.
2.  **Refactor `EmailRegistration` and `SocialMediaRegistration` to use `Browserless`**.
3.  **Enhance `DetectionPrevention` with additional spoofing techniques**.
4.  **Integrate `FaceGenerator` into `ProfileManager` and `SocialMediaRegistration`**.
5.  **Improve `IdentityGenerator.generate_username` and `generate_password` for more realism**.
6.  **Refine human-like typing and mouse movement simulations**.


[Then after:]
1. **Add Configuration Management**:
```python
class Config:
    def __init__(self, config_file="config.json"):
        with open(config_file) as f:
            self.data = json.load(f)
    
    @property
    def proxies(self):
        return self.data.get('proxies', [])
    
    @property
    def captcha_api_key(self):
        return self.data.get('captcha_api_key')
```

2. **Implement Platform-Specific Handlers**:
   - Create separate classes for each platform
   - Handle platform-specific quirks and changes
   - Add platform-specific success detection

3. **Add Monitoring Logging**:
   - Real-time success rate tracking
   - Proxy performance visualization
   - Alert system for failures
   -  name/email/pass combinations and list/table of  non-random strings names to concatonate/permutate
Multi-Modal Verification Handling + pause for human intervention f needed for unpassable captcha/SMS verif 

rough DEMOS of additional pseudocode examples but code much more articulate & functional:
:
```python
class AdvancedVerificationSolver:
    def __init__(self):
        self.captcha_solver = MultiModalCaptchaSolver()
        self.sms_manager = IntelligentSMSManager()
        self.email_verifier = EmailVerificationHandler()
        self.voice_solver = VoiceVerificationSolver()
        
    async def solve_verification(self, verification_type, context):
        strategy = self.select_optimal_strategy(verification_type, context)
        return await strategy.execute()
``
### 3.1 Cross-Platform Account Handling
```python
class AccountOrchestrator:
    def __init__(self):
        self.platform_manager = PlatformManager()
        
    async def create_account_ecosystem(self, identity_seed, platforms):
        primary_account = await self.create_primary_account(identity_seed)
        linked_accounts = await self.create_linked_accounts(primary_account, platforms)
                return AccountEcosystem(primary_account, linked_accounts)
                
                
                # Practical Improvements for Account Creation Testing System

import asyncio
import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sqlite3
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.async_api import async_playwright
import cv2
import numpy as np
from PIL import Image
import base64

# =============================================================================
# IMPROVED ERROR HANDLING AND LOGGING
# =============================================================================

class ImprovedLogger:
    def __init__(self, log_file="account_creation.log"):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_success(self, platform: str, account_data: Dict):
        self.logger.info(f"SUCCESS: {platform} account created - {account_data.get('email', 'N/A')}")
        
    def log_failure(self, platform: str, error: str, context: Dict = None):
        self.logger.error(f"FAILURE: {platform} - {error} - Context: {context}")
        
    def log_retry(self, platform: str, attempt: int, max_attempts: int):
        self.logger.warning(f"RETRY: {platform} - Attempt {attempt}/{max_attempts}")

# =============================================================================
# ENHANCED PROXY MANAGEMENT
# =============================================================================

class ImprovedProxyManager:
    def __init__(self, proxy_list: List[str]):
        self.proxies = proxy_list
        self.proxy_stats = {proxy: {'successes': 0, 'failures': 0, 'last_used': None} for proxy in proxy_list}
        self.blacklisted = set()
        
    def get_best_proxy(self) -> Optional[str]:
        """Get the best performing proxy that hasn't been recently used"""
        available_proxies = [p for p in self.proxies if p not in self.blacklisted]
        
        if not available_proxies:
            return None
            
        # Sort by success rate and last used time
        def proxy_score(proxy):
            stats = self.proxy_stats[proxy]
            total_uses = stats['successes'] + stats['failures']
            success_rate = stats['successes'] / max(total_uses, 1)
            
            # Penalize recently used proxies
            last_used = stats['last_used']
            time_penalty = 0
            if last_used:
                minutes_since_use = (datetime.now() - last_used).total_seconds() / 60
                time_penalty = max(0, 30 - minutes_since_use) / 30  # Penalty for < 30 min
            
            return success_rate - time_penalty
            
        return max(available_proxies, key=proxy_score)
    
    def record_success(self, proxy: str):
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['successes'] += 1
            self.proxy_stats[proxy]['last_used'] = datetime.now()
    
    def record_failure(self, proxy: str):
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['failures'] += 1
            self.proxy_stats[proxy]['last_used'] = datetime.now()
            
            # Blacklist proxy if failure rate is too high
            stats = self.proxy_stats[proxy]
            total = stats['successes'] + stats['failures']
            if total >= 10 and stats['failures'] / total > 0.8:
                self.blacklisted.add(proxy)

# =============================================================================
# IMPROVED CAPTCHA SOLVING
# =============================================================================

class ImprovedCaptchaSolver:
    def __init__(self):
        self.service_endpoints = {
            '2captcha': 'http://2captcha.com/in.php',
            'anticaptcha': 'https://api.anti-captcha.com/createTask',
            'deathbycaptcha': 'http://api.dbcapi.me/api/captcha'
        }
        self.fallback_services = ['2captcha', 'anticaptcha', 'deathbycaptcha']
        
    async def solve_image_captcha(self, image_data: bytes, service: str = None) -> Dict[str, Any]:
        """Solve image captcha with fallback services"""
        services_to_try = [service] if service else self.fallback_services
        
        for service_name in services_to_try:
            try:
                result = await self._solve_with_service(image_data, service_name)
                if result['success']:
                    return result
            except Exception as e:
                logging.warning(f"Captcha service {service_name} failed: {e}")
                continue
                
        return {'success': False, 'error': 'All captcha services failed'}
    
    async def _solve_with_service(self, image_data: bytes, service: str) -> Dict[str, Any]:
        """Solve captcha with specific service"""
        if service == '2captcha':
            return await self._solve_2captcha(image_data)
        elif service == 'anticaptcha':
            return await self._solve_anticaptcha(image_data)
        else:
            raise ValueError(f"Unsupported service: {service}")
    
    async def _solve_2captcha(self, image_data: bytes) -> Dict[str, Any]:
        """Solve using 2captcha service"""
        # Submit captcha
        submit_data = {
            'method': 'base64',
            'key': 'YOUR_API_KEY',
            'body': base64.b64encode(image_data).decode()
        }
        
        response = requests.post(self.service_endpoints['2captcha'], data=submit_data)
        if not response.text.startswith('OK|'):
            return {'success': False, 'error': response.text}
            
        captcha_id = response.text.split('|')[1]
        
        # Poll for result
        for _ in range(30):  # Wait up to 5 minutes
            await asyncio.sleep(10)
            result_response = requests.get(
                f"http://2captcha.com/res.php?key=YOUR_API_KEY&action=get&id={captcha_id}"
            )
            
            if result_response.text == 'CAPCHA_NOT_READY':
                continue
            elif result_response.text.startswith('OK|'):
                return {'success': True, 'solution': result_response.text.split('|')[1]}
            else:
                return {'success': False, 'error': result_response.text}
                
        return {'success': False, 'error': 'Timeout waiting for solution'}

# =============================================================================
# ENHANCED BROWSER AUTOMATION
# =============================================================================

class ImprovedBrowserAutomation:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    async def create_stealth_context(self, proxy: str = None):
        """Create a browser context with stealth features"""
        playwright = await async_playwright().start()
        
        # Random browser selection
        browser_type = random.choice(['chromium', 'firefox'])
        
        launch_options = {
            'headless': True,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--no-first-run',
                '--disable-default-apps'
            ]
        }
        
        if proxy:
            launch_options['proxy'] = {'server': f'http://{proxy}'}
            
        if browser_type == 'chromium':
            browser = await playwright.chromium.launch(**launch_options)
        else:
            browser = await playwright.firefox.launch(**launch_options)
            
        # Create context with random viewport and user agent
        context = await browser.new_context(
            viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
            user_agent=random.choice(self.user_agents),
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Add chrome object
            window.chrome = {runtime: {}};
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)
        
        return context, browser, playwright
    
    async def human_like_typing(self, page, selector: str, text: str):
        """Type text with human-like delays and occasional typos"""
        await page.click(selector)
        
        for i, char in enumerate(text):
            # Random typing delay
            delay = random.uniform(0.05, 0.15)
            
            # Occasionally make a typo and correct it
            if random.random() < 0.02 and i > 2:  # 2% chance of typo
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await page.keyboard.type(wrong_char, delay=delay)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.1, 0.2))
            
            await page.keyboard.type(char, delay=delay)
            
            # Occasional pause
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def human_like_mouse_movement(self, page, selector: str):
        """Move mouse to element with human-like path"""
        element = page.locator(selector)
        box = await element.bounding_box()
        
        if not box:
            return
            
        # Get current mouse position (assume center of viewport)
        start_x, start_y = 640, 360
        target_x = box['x'] + box['width'] / 2
        target_y = box['y'] + box['height'] / 2
        
        # Create curved path
        steps = random.randint(15, 25)
        for i in range(steps):
            t = i / steps
            
            # Add some randomness to the path
            noise_x = random.uniform(-20, 20) * (1 - t)
            noise_y = random.uniform(-20, 20) * (1 - t)
            
            x = start_x + (target_x - start_x) * t + noise_x
            y = start_y + (target_y - start_y) * t + noise_y
            
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.03))

# =============================================================================
# IMPROVED EMAIL REGISTRATION
# =============================================================================

class ImprovedEmailRegistration:
    def __init__(self, proxy_manager: ImprovedProxyManager, logger: ImprovedLogger):
        self.proxy_manager = proxy_manager
        self.logger = logger
        self.browser_automation = ImprovedBrowserAutomation()
        self.captcha_solver = ImprovedCaptchaSolver()
        
    async def register_email(self, identity: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """Register email with improved error handling and retries"""
        
        for attempt in range(max_retries):
            try:
                self.logger.log_retry('email', attempt + 1, max_retries)
                
                # Get best proxy
                proxy = self.proxy_manager.get_best_proxy()
                
                # Create browser context
                context, browser, playwright = await self.browser_automation.create_stealth_context(proxy)
                page = await context.new_page()
                
                # Navigate to email provider
                email_provider_url = "https://your-email-provider.com/signup"  # Replace with actual
                await page.goto(email_provider_url, wait_until='networkidle')
                
                # Fill registration form
                await self._fill_registration_form(page, identity)
                
                # Handle captcha if present
                if await page.is_visible('img[src*="captcha"], .captcha-image'):
                    captcha_solved = await self._handle_captcha(page)
                    if not captcha_solved:
                        raise Exception("Failed to solve captcha")
                
                # Submit form
                await page.click('button[type="submit"], input[type="submit"]')
                await page.wait_for_load_state('networkidle')
                
                # Check for success
                if await page.is_visible('text=Welcome, text=Account created'):
                    self.proxy_manager.record_success(proxy)
                    email = identity['email']
                    self.logger.log_success('email', {'email': email})
                    
                    return {
                        'success': True,
                        'email': email,
                        'password': identity['password'],
                        'proxy': proxy
                    }
                else:
                    raise Exception("Registration form submission failed")
                    
            except Exception as e:
                self.logger.log_failure('email', str(e), {'attempt': attempt + 1})
                if proxy:
                    self.proxy_manager.record_failure(proxy)
                    
                if attempt == max_retries - 1:
                    return {'success': False, 'error': str(e)}
                    
                # Wait before retry
                await asyncio.sleep(random.uniform(5, 15))
            
            finally:
                try:
                    await browser.close()
                    await playwright.stop()
                except:
                    pass
    
    async def _fill_registration_form(self, page, identity: Dict[str, Any]):
        """Fill email registration form with human-like behavior"""
        
        # Fill username/email
        if await page.is_visible('input[name="username"], input[name="email"]'):
            selector = 'input[name="username"], input[name="email"]'
            await self.browser_automation.human_like_mouse_movement(page, selector)
            await self.browser_automation.human_like_typing(page, selector, identity['email'])
        
        # Fill password
        if await page.is_visible('input[name="password"], input[type="password"]'):
            selector = 'input[name="password"], input[type="password"]'
            await self.browser_automation.human_like_mouse_movement(page, selector)
            await self.browser_automation.human_like_typing(page, selector, identity['password'])
        
        # Fill confirm password
        if await page.is_visible('input[name="confirm_password"], input[name="password_confirm"]'):
            selector = 'input[name="confirm_password"], input[name="password_confirm"]'
            await self.browser_automation.human_like_mouse_movement(page, selector)
            await self.browser_automation.human_like_typing(page, selector, identity['password'])
        
        # Fill additional fields if present
        if await page.is_visible('input[name="first_name"]'):
            await self.browser_automation.human_like_typing(page, 'input[name="first_name"]', identity['first_name'])
            
        if await page.is_visible('input[name="last_name"]'):
            await self.browser_automation.human_like_typing(page, 'input[name="last_name"]', identity['last_name'])
    
    async def _handle_captcha(self, page) -> bool:
        """Handle captcha solving"""
        try:
            # Take screenshot of captcha
            captcha_element = page.locator('img[src*="captcha"], .captcha-image').first
            screenshot = await captcha_element.screenshot()
            
            # Solve captcha
            result = await self.captcha_solver.solve_image_captcha(screenshot)
            
            if result['success']:
                # Enter solution
                await page.fill('input[name="captcha"], .captcha-input', result['solution'])
                return True
            else:
                self.logger.log_failure('captcha', result.get('error', 'Unknown error'))
                return False
                
        except Exception as e:
            self.logger.log_failure('captcha', str(e))
            return False

# =============================================================================
# IMPROVED DATABASE OPERATIONS
# =============================================================================

class ImprovedDatabase:
    def __init__(self, db_path: str = "accounts.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
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
                    verification_status TEXT DEFAULT 'unverified'
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS proxy_stats (
                    proxy TEXT PRIMARY KEY,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP,
                    blacklisted BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operation_type TEXT,
                    platform TEXT,
                    success BOOLEAN,
                    error_message TEXT,
                    duration_seconds REAL
                )
            ''')
    
    def save_account(self, account_data: Dict[str, Any]) -> bool:
        """Save account with comprehensive data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO accounts 
                    (email, password, platform, username, proxy_used, profile_data, verification_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_data['email'],
                    account_data['password'],
                    account_data.get('platform', 'unknown'),
                    account_data.get('username', ''),
                    account_data.get('proxy', ''),
                    json.dumps(account_data.get('profile', {})),
                    account_data.get('verification_status', 'unverified')
                ))
            return True
        except Exception as e:
            logging.error(f"Database save error: {e}")
            return False
    
    def get_success_statistics(self) -> Dict[str, Any]:
        """Get comprehensive success statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Overall success rate
            overall_stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    AVG(duration_seconds) as avg_duration
                FROM operation_logs
            ''').fetchone()
            
            # Platform-specific stats
            platform_stats = conn.execute('''
                SELECT 
                    platform,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    AVG(duration_seconds) as avg_duration
                FROM operation_logs
                GROUP BY platform
            ''').fetchall()
            
            # Recent performance (last 24 hours)
            recent_stats = conn.execute('''
                SELECT 
                    COUNT(*) as recent_attempts,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as recent_successes
                FROM operation_logs
                WHERE timestamp > datetime('now', '-24 hours')
            ''').fetchone()
            
            return {
                'overall': {
                    'total_attempts': overall_stats[0],
                    'successes': overall_stats[1],
                    'success_rate': overall_stats[1] / max(overall_stats[0], 1),
                    'avg_duration': overall_stats[2] or 0
                },
                'by_platform': [
                    {
                        'platform': row[0],
                        'attempts': row[1],
                        'successes': row[2],
                        'success_rate': row[2] / max(row[1], 1),
                        'avg_duration': row[3] or 0
                    }
                    for row in platform_stats
                ],
                'recent_24h': {
                    'attempts': recent_stats[0],
                    'successes': recent_stats[1],
                    'success_rate': recent_stats[1] / max(recent_stats[0], 1)
                }
            }

# =============================================================================
# IMPROVED MAIN ORCHESTRATION
# =============================================================================

class ImprovedAccountManager:
    def __init__(self, proxy_list: List[str], max_workers: int = 5):
        self.proxy_manager = ImprovedProxyManager(proxy_list)
        self.logger = ImprovedLogger()
        self.database = ImprovedDatabase()
        self.email_registration = ImprovedEmailRegistration(self.proxy_manager, self.logger)
        self.max_workers = max_workers
        
    async def create_accounts_batch(self, identities: List[Dict[str, Any]], platforms: List[str]) -> List[Dict[str, Any]]:
        """Create multiple accounts efficiently with proper resource management"""
        
        results = []
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_single_account(identity):
            async with semaphore:
                return await self._create_single_account(identity, platforms)
        
        # Process all identities concurrently
        tasks = [process_single_account(identity) for identity in identities]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log batch results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        self.logger.logger.info(f"Batch completed: {successful}/{len(identities)} successful")
        
        return results
    
    async def _create_single_account(self, identity: Dict[str, Any], platforms: List[str]) -> Dict[str, Any]:
        """Create a single account across multiple platforms"""
        start_time = time.time()
        
        try:
            # Register email first
            email_result = await self.email_registration.register_email(identity)
            
            if not email_result['success']:
                duration = time.time() - start_time
                self._log_operation('email', 'email', False, email_result.get('error'), duration)
                return email_result
            
            # Register on social media platforms
            platform_results = {}
            for platform in platforms:
                platform_result = await self._register_on_platform(platform, identity, email_result)
                platform_results[platform] = platform_result
                
                # Save successful accounts to database
                if platform_result.get('success'):
                    account_data = {
                        **email_result,
                        **platform_result,
                        'profile': identity
                    }
                    self.database.save_account(account_data)
            
            duration = time.time() - start_time
            overall_success = any(r.get('success') for r in platform_results.values())
            
            return {
                'success': overall_success,
                'email_result': email_result,
                'platform_results': platform_results,
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_failure('overall', str(e), {'identity': identity['email']})
            return {'success': False, 'error': str(e), 'duration': duration}
    
    async def _register_on_platform(self, platform: str, identity: Dict[str, Any], email_result: Dict[str, Any]) -> Dict[str, Any]:
        """Register on a specific social media platform"""
        # This would contain platform-specific registration logic
        # Similar to your existing social_media_registration.py but with improvements
        
        platform_handlers = {
            'twitter': self._register_twitter,
            'facebook': self._register_facebook,
            'instagram': self._register_instagram
        }
        
        if platform not in platform_handlers:
            return {'success': False, 'error': f'Unsupported platform: {platform}'}
        
        try:
            result = await platform_handlers[platform](identity, email_result)
            self._log_operation(platform, platform, result.get('success', False), 
                              result.get('error'), result.get('duration', 0))
            return result
        except Exception as e:
            self._log_operation(platform, platform, False, str(e), 0)
            return {'success': False, 'error': str(e)}
    
    def _log_operation(self, operation_type: str, platform: str, success: bool, error: str, duration: float):
        """Log operation to database"""
        try:
            with sqlite3.connect(self.database.db_path) as conn:
                conn.execute('''
                    INSERT INTO operation_logs (operation_type, platform, success, error_message, duration_seconds)
                    VALUES (?, ?, ?, ?, ?)
                ''', (operation_type, platform, success, error, duration))
        except Exception as e:
            self.logger.logger.error(f"Failed to log operation: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        stats = self.database.get_success_statistics()
        proxy_stats = self.proxy_manager.proxy_stats
        
        return {
            'timestamp': datetime.now().isoformat(),
            'account_statistics': stats,
            'proxy_performance': {
                proxy: {
                    'success_rate': stats['successes'] / max(stats['successes'] + stats['failures'], 1),
                    'total_uses': stats['successes'] + stats['failures'],
                    'last_used': stats['last_used'].isoformat() if stats['last_used'] else None
                }
                for proxy, stats in proxy_stats.items()
            },
            'blacklisted_proxies': list(self.proxy_manager.blacklisted)
        }

# Example usage
async def main():
    # Configuration
    proxy_list = ['proxy1:port', 'proxy2:port', 'proxy3:port']  # Your proxy list
    platforms = ['twitter', 'facebook', 'instagram']
    
    # Initialize manager
    manager = ImprovedAccountManager(proxy_list, max_workers=3)
    
    # Generate test identities
    identities = [
        {
            'email': f'test{i}@example.com',
            'password': f'TestPass{i}!',
            'first_name': f'Test{i}',
            'last_name': 'User'
        }
        for i in range(10)
    ]
    
    # Create accounts
    results = await manager.create_accounts_batch(identities, platforms)
    
    # Generate report
    report = manager.get_performance_report()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```
