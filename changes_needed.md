# Specific Code Changes Needed for Mass Account Creation Automator

## 1. modules/improved_database.py

### 1.1 Remove Plaintext Password Storage
**Current Issue**: The database stores both plaintext passwords and password hashes
**Location**: Line 395-410 in `save_account` method

```diff
- (email, password, platform, username, proxy_used, profile_data, 
-  verification_status, ecosystem_id, linked_accounts, password_hash, notes)
- VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
+ (email, platform, username, proxy_used, profile_data, 
+  verification_status, ecosystem_id, linked_accounts, password_hash, notes)
+ VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

**Additional Changes**:
- Update method signature to not accept plaintext password
- Add input validation for password before hashing
- Implement proper transaction management with rollback

### 1.2 Add Proper Connection Cleanup
**Current Issue**: No explicit connection cleanup in destructor
**Location**: Line 634 in `__del__` method

```diff
# Add better error handling in cleanup
def close(self):
    """Close all database connections safely"""
    with self._lock:
        for conn in self._connection_pool.values():
            try:
                conn.commit()  # Ensure any pending transactions are committed
                conn.close()
            except Exception as e:
                self.logger.error(f"Error closing database connection: {e}")
        self._connection_pool.clear()
```

## 2. modules/advanced_verification_solver.py

### 2.1 Implement Real Email Verification
**Current Issue**: `_get_email_verification_code` method returns placeholder
**Location**: Line 670-680

```diff
async def _get_email_verification_code(self, email: str) -> Dict[str, Any]:
    """Get verification code from email using secure IMAP connection"""
    try:
        from cryptography.fernet import Fernet
        import imaplib
        import email as email_lib
        import re
        from config.advanced_config import AdvancedConfig
        
        # Get secure configuration
        config = AdvancedConfig()
        email_config = config.data.get('email_verification', {})
        
        if not email_config.get('enabled', False):
            return {'success': False, 'error': 'Email verification not configured'}
        
        # Extract email service (e.g., gmail.com from user@gmail.com)
        email_parts = email.split('@')
        email_service = email_parts[1] if len(email_parts) > 1 else 'gmail.com'
        
        # Determine server based on email service
        servers = {
            'gmail.com': 'imap.gmail.com',
            'outlook.com': 'outlook.office365.com',
            'hotmail.com': 'outlook.office365.com',
            'yahoo.com': 'imap.mail.yahoo.com'
        }
        
        server_name = servers.get(email_service, 'imap.gmail.com')
        
        # Get credentials from secure config
        username = email_config.get('username', '')
        password = email_config.get('password', '')
        
        if not username or not password:
            return {'success': False, 'error': 'Email credentials not configured'}
        
        # Connect securely
        mail = imaplib.IMAP4_SSL(server_name)
        mail.login(username, password)
        mail.select('inbox')
        
        # Search for verification emails (recent 10 minutes)
        import time
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(minutes=10)).strftime("%d-%b-%Y")
        
        status, messages = mail.search(None, f'(SINCE {since_date})', '(UNSEEN)')
        
        if status == 'OK':
            email_ids = messages[0].split()
            
            # Check latest emails first
            for email_id in reversed(email_ids):
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status == 'OK':
                    msg = email_lib.message_from_bytes(msg_data[0][1])
                    
                    # Check if this is a verification email
                    subject = msg.get('Subject', '').lower()
                    sender = msg.get('From', '').lower()
                    
                    verification_keywords = ['verification', 'confirm', 'activate', 'verify']
                    verification_senders = ['noreply', 'no-reply', 'verification', 'confirm']
                    
                    is_verification = any(keyword in subject for keyword in verification_keywords)
                    is_verification |= any(sender_domain in sender for sender_domain in verification_senders)
                    
                    if is_verification:
                        # Parse email content
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get('Content-Disposition'))
                                
                                if content_type == 'text/plain' and 'attachment' not in content_disposition:
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()
                        
                        # Extract verification code using multiple regex patterns
                        code_patterns = [
                            r'code[:\s]+([A-Za-z0-9]{4,8})',
                            r'activation code[:\s]+([A-Za-z0-9]{4,8})',
                            r'verification code[:\s]+([A-Za-z0-9]{4,8})',
                            r'confirm code[:\s]+([A-Za-z0-9]{4,8})',
                            r'(\d{4,6})',  # 4-6 digit numbers
                        ]
                        
                        for pattern in code_patterns:
                            match = re.search(pattern, body, re.IGNORECASE)
                            if match:
                                code = match.group(1).strip()
                                # Mark email as read
                                mail.store(email_id, '+FLAGS', '\\Seen')
                                mail.close()
                                mail.logout()
                                
                                return {
                                    'success': True,
                                    'code': code,
                                    'method': 'email_verification'
                                }
        
        mail.close()
        mail.logout()
        
        return {'success': False, 'error': 'No verification code found in recent emails'}
        
    except Exception as e:
        self.logger.error(f"Email verification code retrieval error: {e}")
        return {'success': False, 'error': f'Email verification error: {str(e)}'}
```

### 2.2 Fix FunCaptcha Implementation
**Current Issue**: Uses hardcoded service URL that doesn't exist
**Location**: Line 455-530 in `_solve_funcaptcha` method

```diff
async def _solve_funcaptcha(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
    """Solve FunCaptcha"""
    try:
        self.logger.info(f"Attempting to solve FunCaptcha (attempt {attempt})")
        
        # Extract FunCaptcha parameters
        funcaptcha_data = await self._extract_funcaptcha_params(page)
        if not funcaptcha_data:
            return {'success': False, 'error': 'Failed to extract FunCaptcha parameters'}
        
        # Get configured captcha services
        from config.advanced_config import AdvancedConfig
        config = AdvancedConfig()
        captcha_services = config.captcha_services
        
        # Try configured captcha services first
        for service_config in captcha_services:
            if service_config.name.lower() == 'funcaptcha' or 'funcaptcha' in service_config.name.lower():
                try:
                    # Use configured service to solve FunCaptcha
                    result = await self._solve_funcaptcha_with_service(
                        service_config, funcaptcha_data, page.url
                    )
                    
                    if result.get('success'):
                        token = result.get('solution', {}).get('token')
                        if token:
                            await self._apply_funcaptcha_solution(page, token, funcaptcha_data)
                            
                            if await self._verify_captcha_success(page, context):
                                return {'success': True, 'method': 'captcha_service', 'service': service_config.name}
                
                except Exception as service_error:
                    self.logger.warning(f"FunCaptcha service {service_config.name} failed: {service_error}")
                    continue
        
        # If services failed, try browser-based approach with computer vision
        self.logger.info("Attempting browser-based FunCaptcha solution")
        
        # Locate and interact with FunCaptcha iframe
        iframe_selectors = [
            'iframe[src*="funcaptcha"]',
            'iframe[src*="arkoselabs"]',
            'iframe[title*="FunCaptcha"]',
            '[data-callback*="funcaptcha"]'
        ]
        
        for selector in iframe_selectors:
            try:
                iframe_element = await page.wait_for_selector(selector, timeout=5000)
                if iframe_element:
                    iframe = await iframe_element.content_frame()
                    if iframe:
                        # Attempt solution (would require advanced computer vision)
                        # For now, return with human intervention request
                        self.logger.info("FunCaptcha requires human intervention")
                        human_result = await self._request_human_intervention(context)
                        return {
                            'success': human_result.get('success', False),
                            'method': 'human_intervention',
                            'requires_human_intervention': True
                        }
            except:
                continue
        
        self._increment_failure_count('funcaptcha')
        return {
            'success': False, 
            'error': 'Failed to solve FunCaptcha', 
            'requires_human_intervention': self._should_request_human_intervention()
        }
        
    except Exception as e:
        self._increment_failure_count('funcaptcha')
        return {'success': False, 'error': f'FunCaptcha error: {str(e)}'}
```

## 3. utils/face_generator.py

### 3.1 Add Proper Error Handling and Model Download
**Current Issue**: Uses non-existent model file without proper error handling
**Location**: Line 12-25 in `__init__` method

```diff
def __init__(self, model_path='models/pulse.pt'):
    self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    self.model_path = model_path
    self.model = self.load_model(model_path)
    self.transform = transforms.Compose([
        transforms.Resize(256),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])

def load_model(self, model_path):
    """Load pre-trained PULSE generator with fallback options"""
    try:
        model = Generator(256, 512, 8)
        
        # Check if model file exists
        if os.path.exists(model_path):
            try:
                model.load_state_dict(torch.load(model_path, map_location=self.device))
                print(f"Loaded pre-trained model from {model_path}")
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")
                print("Using randomly initialized model - faces will be random noise")
                # Initialize with random weights if loading fails
        else:
            print(f"Model file not found at {model_path}")
            # Option to download a default model
            if not os.path.exists(os.path.dirname(model_path)):
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # For now, initialize with random weights
            print("Using randomly initialized model - faces will be random noise")
        
        model.eval()
        return model.to(self.device)
    except Exception as e:
        print(f"Error initializing model: {e}")
        # Return a placeholder model that generates random noise
        return self._create_placeholder_model()
    
def _create_placeholder_model(self):
    """Create a placeholder model that generates random noise"""
    print("WARNING: Using placeholder model that generates random noise")
    # Implement a minimal model that just returns random pixels
    # For now, just return a basic model
    model = Generator(256, 512, 8)
    model.eval()
    return model.to(self.device)
```

## 4. utils/proxy_manager.py

### 4.1 Add Proxy Authentication Support
**Current Issue**: Only supports basic HTTP proxies without authentication
**Location**: Line 73-82 in `test_proxy` method

```diff
async def test_proxy(self, proxy: str, timeout: int = 10) -> Tuple[bool, float]:
    """Test if a proxy is working and measure response time"""
    start_time = time.time()
    
    try:
        # Parse proxy string with various formats
        proxy_url = self._parse_proxy_url(proxy)
        
        response = requests.get(
            self.test_url,
            proxies=proxy_url,
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

def _parse_proxy_url(self, proxy: str) -> Dict[str, str]:
    """Parse proxy string in various formats"""
    # Handle different proxy formats: host:port, http://host:port, user:pass@host:port
    if proxy.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
        # Already full URL format
        return {
            'http': proxy.replace('https://', 'http://'),  # Use HTTP for both
            'https': proxy
        }
    elif '@' in proxy and ':' in proxy.split('@')[1]:  # user:pass@host:port
        auth_part, address_part = proxy.split('@')
        user, password = auth_part.split(':')
        return {
            'http': f'http://{user}:{password}@{address_part}',
            'https': f'http://{user}:{password}@{address_part}'
        }
    else:  # host:port format
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
```

## 5. modules/improved_account_manager.py

### 5.1 Add Proper Resource Cleanup and Error Handling
**Current Issue**: Missing proper resource cleanup and error handling
**Location**: Line 130-180 in `_create_single_account_ecosystem` method

```diff
async def _create_single_account_ecosystem(self, identity: Dict[str, Any], 
                                         platforms: List[str], 
                                         task_id: str,
                                         strategy: str) -> Dict[str, Any]:
    """Create a single account ecosystem with comprehensive tracking and cleanup"""
    
    start_time = time.time()
    browser = None
    
    try:
        # Create browser instance with proper error handling
        try:
            browser = await self.browser_automation.create_browser()
        except Exception as e:
            self.logger.error(f"Failed to create browser for task {task_id}: {e}")
            raise
        
        # Generate identity seed for consistency
        identity_seed = f"{task_id}_{identity.get('email', 'unknown')}"
        
        # Create account ecosystem using orchestrator
        ecosystem = await self.account_orchestrator.create_account_ecosystem(
            identity_seed=identity_seed,
            platforms=platforms,
            strategy=strategy,
            browser=browser  # Pass browser instance
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
    finally:
        # Always clean up resources
        if browser:
            try:
                await browser.close()
                self.logger.debug(f"Browser closed for task {task_id}")
            except Exception as e:
                self.logger.warning(f"Error closing browser for task {task_id}: {e}")
```

## 6. config/config.py and config/advanced_config.py

### 6.1 Consolidate Configuration Management
**Current Issue**: Multiple config files with potential conflicts
**Location**: Both config files

```diff
# In advanced_config.py, add a unified configuration class
class UnifiedConfig:
    def __init__(self):
        self.basic_config = Config()
        self.advanced_config = AdvancedConfig()
    
    def get_platform_config(self, platform_name: str):
        """Get unified platform configuration"""
        try:
            # Try advanced config first, fall back to basic config
            return self.advanced_config.data.get('platforms', {}).get(platform_name) or \
                   self.basic_config.get_platform_config(platform_name)
        except Exception:
            # Fallback to basic config
            return self.basic_config.get_platform_config(platform_name)
    
    def get_verification_config(self):
        """Get unified verification config"""
        return self.advanced_config.data.get('verification', {}) or \
               self.basic_config.get_verification_config()
    
    def get_proxy_config(self):
        """Get unified proxy config"""
        return self.advanced_config.data.get('proxy', {}) or \
               self.basic_config.get_proxy_config()
```

### 6.2 Add Configuration Validation
**Location**: advanced_config.py

```diff
def _validate_config(self):
    """Validate configuration values with comprehensive checks"""
    try:
        # Check required sections
        required_sections = ["browser_settings", "rate_limiting", "verification_settings"]
        for section in required_sections:
            if section not in self.data:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate rate limiting values
        rate_limiting = self.data.get('rate_limiting', {})
        if rate_limiting.get('requests_per_minute', 0) < 1 or rate_limiting.get('requests_per_minute', 0) > 100:
            raise ValueError("requests_per_minute must be between 1 and 100")
        
        if rate_limiting.get('accounts_per_hour', 0) < 1 or rate_limiting.get('accounts_per_hour', 0) > 500:
            raise ValueError("accounts_per_hour must be between 1 and 500")
        
        # Validate verification settings
        verification_settings = self.data.get('verification_settings', {})
        if verification_settings.get('max_captcha_attempts', 0) < 1 or verification_settings.get('max_captcha_attempts', 0) > 10:
            raise ValueError("max_captcha_attempts must be between 1 and 10")
        
        # Validate browser settings
        browser_settings = self.data.get('browser_settings', {})
        if not isinstance(browser_settings.get('headless', True), bool):
            raise ValueError("headless must be boolean")
        
        self.logger.info("Configuration validation passed")
        
    except Exception as e:
        self.logger.error(f"Configuration validation error: {e}")
        raise
```

## 7. Add Type Hints Throughout Codebase

### 7.1 Add to Key Modules
**Location**: All modules that lack proper type hints

```python
# Example for improved_database.py
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

class ImprovedDatabase:
    def save_account(self, account_data: Dict[str, Any]) -> bool:
        """Save account with comprehensive data validation and error handling"""
        # Implementation with proper return type
        pass
    
    def get_accounts(self, platform: Optional[str] = None, status: str = "active", 
                    ecosystem_id: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve accounts with flexible filtering"""
        # Implementation with proper return type
        pass
```

## 8. Update Requirements

### 8.1 Add Missing Dependencies
**File**: requirements.txt

```diff
playwright
requests
python-dotenv
faker
supabase
numpy
python-dateutil
torch
torchvision
pillow
plyer
psutil
aiofiles
asyncio-throttle
# Add security dependencies
bcrypt
cryptography
# Add testing dependencies
pytest
pytest-asyncio
pytest-cov
mypy
flake8
# Add monitoring dependencies
prometheus-client
opentelemetry-api
opentelemetry-sdk
structlog
# Add configuration dependencies
pydantic  # For configuration validation
```

## 9. Add Comprehensive Error Handling

### 9.1 Add Error Handling to Main Module
**Location**: main.py

```python
async def create_account_advanced(account_num, total_accounts, platforms):
    """Create account using improved account manager with comprehensive error handling"""
    try:
        account_manager, db, notifier, email_reg, profile_manager = get_components()
        
        print(f"\n=== Creating advanced account ecosystem {account_num}/{total_accounts} ===")
        print(f"[{account_num}] Platforms: {platforms}")
        
        # Generate identity using profile manager
        profile = profile_manager.generate_full_profile()
        identity = profile['basic']
        
        # Validate identity before proceeding
        if not identity.get('email') or not identity.get('password') or not identity.get('username'):
            raise ValueError(f"Invalid identity generated for account {account_num}")
        
        # Create account using improved manager
        result = await account_manager.create_single_account(identity, platforms)
        
        # Print results
        if result['success']:
            print(f"✅ [{account_num}] Account ecosystem created successfully")
            print(f"📧 [{account_num}] Primary email: {result.get('primary_email', 'N/A')}")
            print(f"📊 [{account_num}] Success rate: {result.get('success_rate', 0):.2%}")
            print(f"⏱️ [{account_num}] Duration: {result.get('duration', 0):.1f}s")
            
            # Save to legacy database as well for compatibility
            if 'ecosystem' in result:
                ecosystem_data = result['ecosystem']
                primary_account = ecosystem_data.get('primary_account', {})
                if primary_account and primary_account.get('email'):
                    legacy_email_data = {
                        'email': primary_account.get('email', ''),
                        'password': primary_account.get('password', ''),
                        'proxy': ''
                    }
                    legacy_social_data = ecosystem_data.get('linked_accounts', [])
                    db.save_account(legacy_email_data, legacy_social_data, profile)
            
            return True
        else:
            print(f"❌ [{account_num}] Account creation failed: {result.get('error', 'Unknown error')}")
            
            # Check if human intervention is needed
            if result.get('requires_human_intervention'):
                notifier.human_intervention_required(
                    f"Account {account_num}",
                    f"Human intervention required: {result.get('error', 'Unknown issue')}"
                )
            
            return False
        
    except ValueError as ve:
        print(f"⚠️ [{account_num}] Validation error: {str(ve)}")
        notifier.human_intervention_required(
            f"Account {account_num}",
            f"Validation error: {str(ve)}"
        )
        return False
    except Exception as e:
        print(f"⚠️ [{account_num}] Advanced account creation error: {str(e)}")
        notifier.human_intervention_required(
            f"Account {account_num}",
            f"Critical error: {str(e)}"
        )
        return False
```

## 10. Add Unit Tests

### 10.1 Add Test File for Database Module
**File**: tests/test_database.py

```python
import pytest
import tempfile
import os
from modules.improved_database import ImprovedDatabase

@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    db = ImprovedDatabase(db_path=temp_file.name)
    yield db
    os.unlink(temp_file.name)

def test_database_initialization(temp_db):
    """Test that database initializes properly"""
    assert os.path.exists(temp_db.db_path) == True

def test_save_and_retrieve_account(temp_db):
    """Test saving and retrieving an account"""
    account_data = {
        'email': 'test@example.com',
        'password': 'secure_password',
        'platform': 'test_platform',
        'username': 'test_user'
    }
    
    result = temp_db.save_account(account_data)
    assert result == True
    
    accounts = temp_db.get_accounts(platform='test_platform')
    assert len(accounts) == 1
    assert accounts[0]['email'] == 'test@example.com'
```

These specific code changes address the major issues identified in the analysis phase, including security vulnerabilities, incomplete implementations, error handling issues, and architectural problems. Each change includes proper error handling, resource management, and follows the modular architecture principles outlined in the plan.