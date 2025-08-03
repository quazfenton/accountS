import asyncio
import random
import time
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from utils.stealth_browser import StealthBrowserAutomation
from modules.advanced_verification_solver import AdvancedVerificationSolver, VerificationContext, VerificationType

@dataclass
class PlatformConfig:
    """Configuration for a specific platform"""
    name: str
    signup_url: str
    selectors: Dict[str, str]
    success_indicators: List[str]
    error_indicators: List[str]
    verification_types: List[VerificationType]
    rate_limit_delay: Tuple[int, int]  # min, max seconds
    requires_phone: bool = False
    requires_email_verification: bool = True
    profile_requirements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.profile_requirements is None:
            self.profile_requirements = {}

class BasePlatformHandler(ABC):
    """Base class for platform-specific registration handlers"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self.browser_automation = StealthBrowserAutomation()
        self.verification_solver = AdvancedVerificationSolver()
        
        # Platform-specific statistics
        self.stats = {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'avg_duration': 0.0,
            'common_errors': {}
        }
    
    @abstractmethod
    async def register_account(self, identity: Dict[str, Any], 
                             profile: Dict[str, Any]) -> Dict[str, Any]:
        """Register account on the platform"""
        pass
    
    async def _navigate_to_signup(self, page) -> bool:
        """Navigate to signup page"""
        try:
            await page.goto(self.config.signup_url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to fully load
            await asyncio.sleep(random.uniform(2, 5))
            
            # Check if we're on the right page
            current_url = page.url
            if 'signup' not in current_url.lower() and 'register' not in current_url.lower():
                self.logger.warning(f"Unexpected URL after navigation: {current_url}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to signup page: {e}")
            return False
    
    async def _fill_basic_form(self, page, identity: Dict[str, Any], 
                              profile: Dict[str, Any]) -> bool:
        """Fill basic registration form"""
        try:
            selectors = self.config.selectors
            
            # Fill email
            if 'email' in selectors and await page.is_visible(selectors['email']):
                await self.browser_automation.human_like_typing(
                    page, selectors['email'], identity['email']
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill username
            if 'username' in selectors and await page.is_visible(selectors['username']):
                username = identity.get('username', identity['email'].split('@')[0])
                await self.browser_automation.human_like_typing(
                    page, selectors['username'], username
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill password
            if 'password' in selectors and await page.is_visible(selectors['password']):
                await self.browser_automation.human_like_typing(
                    page, selectors['password'], identity['password']
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill confirm password
            if 'confirm_password' in selectors and await page.is_visible(selectors['confirm_password']):
                await self.browser_automation.human_like_typing(
                    page, selectors['confirm_password'], identity['password']
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill first name
            if 'first_name' in selectors and await page.is_visible(selectors['first_name']):
                await self.browser_automation.human_like_typing(
                    page, selectors['first_name'], identity['first_name']
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill last name
            if 'last_name' in selectors and await page.is_visible(selectors['last_name']):
                await self.browser_automation.human_like_typing(
                    page, selectors['last_name'], identity['last_name']
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill basic form: {e}")
            return False
    
    async def _handle_verification_challenges(self, page) -> Dict[str, Any]:
        """Handle verification challenges that appear during registration"""
        try:
            # Check for different types of verification
            for verification_type in self.config.verification_types:
                if await self._is_verification_present(page, verification_type):
                    self.logger.info(f"Detected {verification_type.value} verification")
                    
                    context = VerificationContext(
                        verification_type=verification_type,
                        platform=self.config.name,
                        page_url=page.url,
                        element_selectors=self._get_verification_selectors(verification_type),
                        metadata={'platform': self.config.name}
                    )
                    
                    result = await self.verification_solver.solve_verification(context, page)
                    
                    if result['success']:
                        return result
                    elif result.get('requires_human_intervention'):
                        return result
            
            # No verification challenges detected
            return {'success': True, 'method': 'none'}
            
        except Exception as e:
            self.logger.error(f"Error handling verification challenges: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _is_verification_present(self, page, verification_type: VerificationType) -> bool:
        """Check if a specific verification type is present"""
        verification_selectors = {
            VerificationType.CAPTCHA_IMAGE: ['img[src*="captcha"]', '.captcha-image'],
            VerificationType.RECAPTCHA: ['iframe[src*="recaptcha"]', '.g-recaptcha'],
            VerificationType.HCAPTCHA: ['iframe[src*="hcaptcha"]', '.h-captcha'],
            VerificationType.SMS: ['input[type="tel"]', 'input[placeholder*="phone"]'],
            VerificationType.EMAIL: ['text=verify your email', 'text=check your email']
        }
        
        selectors = verification_selectors.get(verification_type, [])
        
        for selector in selectors:
            if await page.is_visible(selector):
                return True
        
        return False
    
    def _get_verification_selectors(self, verification_type: VerificationType) -> Dict[str, str]:
        """Get platform-specific selectors for verification elements"""
        # This can be overridden by specific platform handlers
        return {
            'phone_input': 'input[type="tel"], input[name="phone"]',
            'code_input': 'input[name="code"], input[placeholder*="code"]',
            'send_button': 'button:has-text("Send"), button:has-text("Verify")',
            'submit_button': 'button[type="submit"], input[type="submit"]',
            'captcha_image': 'img[src*="captcha"], .captcha-image',
            'captcha_input': 'input[name="captcha"], input[placeholder*="captcha"]'
        }
    
    async def _submit_form(self, page) -> bool:
        """Submit the registration form"""
        try:
            selectors = self.config.selectors
            
            # Try different submit methods
            submit_selectors = [
                selectors.get('submit'),
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign up")',
                'button:has-text("Create")',
                'button:has-text("Register")',
                'button:has-text("Join")'
            ]
            
            for selector in submit_selectors:
                if not selector:
                    continue
                
                try:
                    if await page.is_visible(selector):
                        await self.browser_automation.human_like_mouse_movement(page, selector)
                        await asyncio.sleep(random.uniform(1, 3))
                        await page.click(selector)
                        await asyncio.sleep(random.uniform(2, 5))
                        return True
                except:
                    continue
            
            # Fallback: try pressing Enter
            await page.keyboard.press('Enter')
            await asyncio.sleep(random.uniform(2, 5))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to submit form: {e}")
            return False
    
    async def _check_registration_result(self, page) -> Dict[str, Any]:
        """Check if registration was successful"""
        try:
            # Wait for page to load
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check for success indicators
            for indicator in self.config.success_indicators:
                if await page.is_visible(indicator):
                    return {
                        'success': True,
                        'status': 'created',
                        'message': 'Account created successfully'
                    }
            
            # Check for error indicators
            for indicator in self.config.error_indicators:
                if await page.is_visible(indicator):
                    error_text = await page.text_content(indicator)
                    return {
                        'success': False,
                        'error': f'Registration error: {error_text}',
                        'retry_recommended': 'username' in error_text.lower()
                    }
            
            # Check URL for success indicators
            current_url = page.url.lower()
            success_url_indicators = ['welcome', 'success', 'verify', 'confirm']
            
            for indicator in success_url_indicators:
                if indicator in current_url:
                    return {
                        'success': True,
                        'status': 'created',
                        'message': f'Account created (URL indicates success: {indicator})'
                    }
            
            # Default: check page title and content
            page_title = await page.title()
            page_content = await page.content()
            
            # Look for common success patterns
            success_patterns = ['welcome', 'success', 'created', 'verify', 'confirm']
            error_patterns = ['error', 'failed', 'invalid', 'unavailable']
            
            title_lower = page_title.lower()
            content_lower = page_content.lower()
            
            for pattern in success_patterns:
                if pattern in title_lower or pattern in content_lower:
                    return {
                        'success': True,
                        'status': 'created',
                        'message': f'Account likely created (found pattern: {pattern})'
                    }
            
            for pattern in error_patterns:
                if pattern in title_lower:
                    return {
                        'success': False,
                        'error': f'Registration likely failed (found pattern: {pattern})',
                        'page_title': page_title
                    }
            
            # Unable to determine result
            return {
                'success': False,
                'error': 'Could not determine registration result',
                'page_url': page.url,
                'page_title': page_title
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking registration result: {str(e)}'
            }
    
    def _update_stats(self, success: bool, duration: float, error: str = None):
        """Update platform statistics"""
        self.stats['attempts'] += 1
        
        if success:
            self.stats['successes'] += 1
        else:
            self.stats['failures'] += 1
            if error:
                error_key = error[:50]  # Truncate long errors
                self.stats['common_errors'][error_key] = \
                    self.stats['common_errors'].get(error_key, 0) + 1
        
        # Update average duration
        total_duration = self.stats['avg_duration'] * (self.stats['attempts'] - 1) + duration
        self.stats['avg_duration'] = total_duration / self.stats['attempts']
    
    def get_stats(self) -> Dict[str, Any]:
        """Get platform statistics"""
        success_rate = self.stats['successes'] / max(self.stats['attempts'], 1)
        
        return {
            'platform': self.config.name,
            'attempts': self.stats['attempts'],
            'successes': self.stats['successes'],
            'failures': self.stats['failures'],
            'success_rate': success_rate,
            'avg_duration': self.stats['avg_duration'],
            'common_errors': sorted(
                self.stats['common_errors'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

class TwitterHandler(BasePlatformHandler):
    """Twitter-specific registration handler"""
    
    def __init__(self):
        config = PlatformConfig(
            name='twitter',
            signup_url='https://twitter.com/i/flow/signup',
            selectors={
                'email': 'input[name="email"]',
                'name': 'input[name="name"]',
                'phone': 'input[name="phone_number"]',
                'next': 'div[role="button"]:has-text("Next")',
                'submit': 'div[role="button"]:has-text("Sign up")',
                'code_input': 'input[name="verfication_code"]'
            },
            success_indicators=[
                'text=What are you interested in?',
                'text=Follow some accounts',
                'text=Welcome to Twitter'
            ],
            error_indicators=[
                'text=Something went wrong',
                'text=Try again',
                'text=Email has already been taken'
            ],
            verification_types=[
                VerificationType.SMS,
                VerificationType.EMAIL,
                VerificationType.RECAPTCHA
            ],
            rate_limit_delay=(300, 900),  # 5-15 minutes
            requires_phone=True,
            profile_requirements={
                'bio_length': 160,
                'username_style': 'short'
            }
        )
        super().__init__(config)
    
    async def register_account(self, identity: Dict[str, Any], 
                             profile: Dict[str, Any]) -> Dict[str, Any]:
        """Register Twitter account"""
        start_time = time.time()
        
        try:
            # Create browser context
            context, browser, playwright = await self.browser_automation.create_stealth_context()
            page = await context.new_page()
            
            try:
                # Navigate to signup
                if not await self._navigate_to_signup(page):
                    raise Exception("Failed to navigate to signup page")
                
                # Fill name field
                if await page.is_visible(self.config.selectors['name']):
                    full_name = f"{identity['first_name']} {identity['last_name']}"
                    await self.browser_automation.human_like_typing(
                        page, self.config.selectors['name'], full_name
                    )
                
                # Fill email
                if await page.is_visible(self.config.selectors['email']):
                    await self.browser_automation.human_like_typing(
                        page, self.config.selectors['email'], identity['email']
                    )
                
                # Click Next
                if await page.is_visible(self.config.selectors['next']):
                    await page.click(self.config.selectors['next'])
                    await asyncio.sleep(random.uniform(2, 4))
                
                # Handle verification challenges
                verification_result = await self._handle_verification_challenges(page)
                if not verification_result['success']:
                    if verification_result.get('requires_human_intervention'):
                        raise Exception("Human intervention required for verification")
                    else:
                        raise Exception(f"Verification failed: {verification_result.get('error', 'Unknown error')}")
                
                # Check final result
                result = await self._check_registration_result(page)
                
                duration = time.time() - start_time
                self._update_stats(result['success'], duration, result.get('error'))
                
                return {
                    **result,
                    'platform': 'twitter',
                    'duration': duration,
                    'username': identity.get('username', ''),
                    'verification_method': verification_result.get('method')
                }
                
            finally:
                await context.close()
                await browser.close()
                await playwright.stop()
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats(False, duration, str(e))
            
            return {
                'success': False,
                'platform': 'twitter',
                'error': str(e),
                'duration': duration
            }

class FacebookHandler(BasePlatformHandler):
    """Facebook-specific registration handler"""
    
    def __init__(self):
        config = PlatformConfig(
            name='facebook',
            signup_url='https://www.facebook.com/reg/',
            selectors={
                'first_name': 'input[name="firstname"]',
                'last_name': 'input[name="lastname"]',
                'email': 'input[name="reg_email__"]',
                'password': 'input[name="reg_passwd__"]',
                'birthday_day': 'select[name="birthday_day"]',
                'birthday_month': 'select[name="birthday_month"]',
                'birthday_year': 'select[name="birthday_year"]',
                'gender': 'input[name="sex"]',
                'submit': 'button[name="websubmit"]'
            },
            success_indicators=[
                'text=Find friends',
                'text=Welcome to Facebook',
                'text=Add a profile picture'
            ],
            error_indicators=[
                'text=This email is already in use',
                'text=Please enter a valid email',
                'text=Something went wrong'
            ],
            verification_types=[
                VerificationType.CAPTCHA_IMAGE,
                VerificationType.SMS,
                VerificationType.EMAIL
            ],
            rate_limit_delay=(600, 1800),  # 10-30 minutes
            requires_phone=False,
            profile_requirements={
                'bio_length': 101,
                'username_style': 'real_name'
            }
        )
        super().__init__(config)
    
    async def register_account(self, identity: Dict[str, Any], 
                             profile: Dict[str, Any]) -> Dict[str, Any]:
        """Register Facebook account"""
        start_time = time.time()
        
        try:
            context, browser, playwright = await self.browser_automation.create_stealth_context()
            page = await context.new_page()
            
            try:
                if not await self._navigate_to_signup(page):
                    raise Exception("Failed to navigate to signup page")
                
                # Fill basic form
                if not await self._fill_basic_form(page, identity, profile):
                    raise Exception("Failed to fill basic form")
                
                # Fill birthday
                birth_year = random.randint(1980, 2000)
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)
                
                if await page.is_visible(self.config.selectors['birthday_day']):
                    await page.select_option(self.config.selectors['birthday_day'], str(birth_day))
                
                if await page.is_visible(self.config.selectors['birthday_month']):
                    await page.select_option(self.config.selectors['birthday_month'], str(birth_month))
                
                if await page.is_visible(self.config.selectors['birthday_year']):
                    await page.select_option(self.config.selectors['birthday_year'], str(birth_year))
                
                # Select gender
                gender_value = "1" if identity.get('gender', 'M') == 'M' else "2"
                gender_selector = f'input[name="sex"][value="{gender_value}"]'
                if await page.is_visible(gender_selector):
                    await page.click(gender_selector)
                
                # Handle verification
                verification_result = await self._handle_verification_challenges(page)
                if not verification_result['success']:
                    if verification_result.get('requires_human_intervention'):
                        raise Exception("Human intervention required")
                    else:
                        raise Exception(f"Verification failed: {verification_result.get('error')}")
                
                # Submit form
                if not await self._submit_form(page):
                    raise Exception("Failed to submit form")
                
                # Check result
                result = await self._check_registration_result(page)
                
                duration = time.time() - start_time
                self._update_stats(result['success'], duration, result.get('error'))
                
                return {
                    **result,
                    'platform': 'facebook',
                    'duration': duration,
                    'username': identity.get('username', ''),
                    'verification_method': verification_result.get('method')
                }
                
            finally:
                await context.close()
                await browser.close()
                await playwright.stop()
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats(False, duration, str(e))
            
            return {
                'success': False,
                'platform': 'facebook',
                'error': str(e),
                'duration': duration
            }

class InstagramHandler(BasePlatformHandler):
    """Instagram-specific registration handler"""
    
    def __init__(self):
        config = PlatformConfig(
            name='instagram',
            signup_url='https://www.instagram.com/accounts/emailsignup/',
            selectors={
                'email': 'input[name="emailOrPhone"]',
                'full_name': 'input[name="fullName"]',
                'username': 'input[name="username"]',
                'password': 'input[name="password"]',
                'submit': 'button[type="submit"]'
            },
            success_indicators=[
                'text=Find people to follow',
                'text=Welcome to Instagram',
                'text=Add a profile photo'
            ],
            error_indicators=[
                'text=This username isn\'t available',
                'text=Another account is using the same email',
                'text=Something went wrong'
            ],
            verification_types=[
                VerificationType.CAPTCHA_IMAGE,
                VerificationType.SMS,
                VerificationType.EMAIL
            ],
            rate_limit_delay=(300, 1200),  # 5-20 minutes
            requires_phone=False,
            profile_requirements={
                'bio_length': 150,
                'username_style': 'creative'
            }
        )
        super().__init__(config)
    
    async def register_account(self, identity: Dict[str, Any], 
                             profile: Dict[str, Any]) -> Dict[str, Any]:
        """Register Instagram account"""
        start_time = time.time()
        
        try:
            context, browser, playwright = await self.browser_automation.create_stealth_context()
            page = await context.new_page()
            
            try:
                if not await self._navigate_to_signup(page):
                    raise Exception("Failed to navigate to signup page")
                
                # Fill form fields
                if await page.is_visible(self.config.selectors['email']):
                    await self.browser_automation.human_like_typing(
                        page, self.config.selectors['email'], identity['email']
                    )
                
                if await page.is_visible(self.config.selectors['full_name']):
                    full_name = f"{identity['first_name']} {identity['last_name']}"
                    await self.browser_automation.human_like_typing(
                        page, self.config.selectors['full_name'], full_name
                    )
                
                if await page.is_visible(self.config.selectors['username']):
                    username = identity.get('username', identity['email'].split('@')[0])
                    await self.browser_automation.human_like_typing(
                        page, self.config.selectors['username'], username
                    )
                
                if await page.is_visible(self.config.selectors['password']):
                    await self.browser_automation.human_like_typing(
                        page, self.config.selectors['password'], identity['password']
                    )
                
                # Handle verification
                verification_result = await self._handle_verification_challenges(page)
                if not verification_result['success']:
                    if verification_result.get('requires_human_intervention'):
                        raise Exception("Human intervention required")
                    else:
                        raise Exception(f"Verification failed: {verification_result.get('error')}")
                
                # Submit
                if not await self._submit_form(page):
                    raise Exception("Failed to submit form")
                
                # Check result
                result = await self._check_registration_result(page)
                
                duration = time.time() - start_time
                self._update_stats(result['success'], duration, result.get('error'))
                
                return {
                    **result,
                    'platform': 'instagram',
                    'duration': duration,
                    'username': username,
                    'verification_method': verification_result.get('method')
                }
                
            finally:
                await context.close()
                await browser.close()
                await playwright.stop()
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats(False, duration, str(e))
            
            return {
                'success': False,
                'platform': 'instagram',
                'error': str(e),
                'duration': duration
            }

# Platform handler factory
class PlatformHandlerFactory:
    """Factory for creating platform handlers"""
    
    _handlers = {
        'twitter': TwitterHandler,
        'facebook': FacebookHandler,
        'instagram': InstagramHandler
    }
    
    @classmethod
    def create_handler(cls, platform: str) -> BasePlatformHandler:
        """Create a handler for the specified platform"""
        if platform not in cls._handlers:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return cls._handlers[platform]()
    
    @classmethod
    def get_supported_platforms(cls) -> List[str]:
        """Get list of supported platforms"""
        return list(cls._handlers.keys())
    
    @classmethod
    def register_handler(cls, platform: str, handler_class):
        """Register a new platform handler"""
        cls._handlers[platform] = handler_class