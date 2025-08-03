import asyncio
import random
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.stealth_browser import StealthBrowserAutomation
from utils.proxy_manager import ImprovedProxyManager
from utils.advanced_captcha_solver import AdvancedCaptchaSolver, CaptchaType
from utils.monitoring import MetricsCollector, AccountCreationMetric

class ImprovedEmailRegistration:
    def __init__(self, proxy_manager: ImprovedProxyManager = None, metrics_collector: MetricsCollector = None):
        self.logger = logging.getLogger(__name__)
        self.browser_automation = StealthBrowserAutomation()
        self.captcha_solver = AdvancedCaptchaSolver()
        self.proxy_manager = proxy_manager
        self.metrics_collector = metrics_collector
        
        # Email provider configurations
        self.email_providers = {
            'gmail': {
                'url': 'https://accounts.google.com/signup/v2/webcreateaccount',
                'selectors': {
                    'first_name': 'input[name="firstName"]',
                    'last_name': 'input[name="lastName"]',
                    'username': 'input[name="Username"]',
                    'password': 'input[name="Passwd"]',
                    'confirm_password': 'input[name="ConfirmPasswd"]',
                    'submit': 'button[type="submit"]',
                    'next': 'button:has-text("Next")',
                    'captcha_image': 'img[src*="captcha"]',
                    'captcha_input': 'input[name="ca"]'
                },
                'success_indicators': [
                    'text=Welcome',
                    'text=Verify your phone number',
                    'text=Choose your settings'
                ],
                'error_indicators': [
                    'text=Username not available',
                    'text=Try a different username',
                    'text=This username isn\'t available'
                ]
            },
            'yahoo': {
                'url': 'https://login.yahoo.com/account/create',
                'selectors': {
                    'first_name': 'input[name="firstName"]',
                    'last_name': 'input[name="lastName"]',
                    'username': 'input[name="userId"]',
                    'password': 'input[name="password"]',
                    'submit': 'button[type="submit"]',
                    'captcha_image': '.captcha-container img',
                    'captcha_input': 'input[name="captchaAnswer"]'
                },
                'success_indicators': [
                    'text=Let\'s secure your account',
                    'text=Add your mobile number'
                ],
                'error_indicators': [
                    'text=This ID is not available',
                    'text=Please choose a different Yahoo ID'
                ]
            },
            'outlook': {
                'url': 'https://signup.live.com/',
                'selectors': {
                    'username': 'input[name="MemberName"]',
                    'password': 'input[name="Password"]',
                    'first_name': 'input[name="FirstName"]',
                    'last_name': 'input[name="LastName"]',
                    'submit': 'input[type="submit"]',
                    'next': 'input[value="Next"]'
                },
                'success_indicators': [
                    'text=Help us protect your account',
                    'text=Add security info'
                ],
                'error_indicators': [
                    'text=That Microsoft account doesn\'t exist',
                    'text=Someone already has that username'
                ]
            }
        }
    
    async def register_email(self, identity: Dict[str, Any], provider: str = 'gmail', max_retries: int = 3) -> Dict[str, Any]:
        """Register email with comprehensive error handling and human-like behavior"""
        start_time = time.time()
        
        for attempt in range(max_retries):
            proxy = None
            context = None
            browser = None
            playwright = None
            
            try:
                self.logger.info(f"Email registration attempt {attempt + 1}/{max_retries} for {identity.get('email', 'unknown')}")
                
                # Get best proxy if available
                if self.proxy_manager:
                    proxy = await self.proxy_manager.get_best_proxy()
                    if not proxy:
                        self.logger.warning("No available proxies, proceeding without proxy")
                
                # Create stealth browser context
                context, browser, playwright = await self.browser_automation.create_stealth_context(proxy)
                page = await context.new_page()
                
                # Set up page monitoring
                await self._setup_page_monitoring(page)
                
                # Navigate to email provider
                provider_config = self.email_providers.get(provider, self.email_providers['gmail'])
                await page.goto(provider_config['url'], wait_until='networkidle', timeout=30000)
                
                # Simulate human behavior - look around the page
                await self.browser_automation.simulate_reading_behavior(page)
                
                # Fill registration form
                success = await self._fill_registration_form(page, identity, provider_config)
                if not success:
                    raise Exception("Failed to fill registration form")
                
                # Handle captcha if present
                captcha_solved = await self._handle_captcha_comprehensive(page, provider_config)
                if captcha_solved is False:  # Explicitly check for False (None means no captcha)
                    raise Exception("Failed to solve captcha")
                
                # Submit form with human-like behavior
                await self._submit_form_human_like(page, provider_config)
                
                # Wait for response and check result
                result = await self._check_registration_result(page, provider_config, identity)
                
                if result['success']:
                    # Record success metrics
                    if self.proxy_manager and proxy:
                        self.proxy_manager.record_success(proxy, time.time() - start_time)
                    
                    if self.metrics_collector:
                        metric = AccountCreationMetric(
                            timestamp=datetime.now(),
                            platform='email',
                            success=True,
                            proxy_used=proxy,
                            captcha_solved=captcha_solved is True,
                            creation_time_seconds=time.time() - start_time
                        )
                        self.metrics_collector.record_account_creation(metric)
                    
                    self.logger.info(f"Email registration successful: {result['email']}")
                    return result
                else:
                    raise Exception(result.get('error', 'Registration failed'))
                    
            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Email registration attempt {attempt + 1} failed: {error_msg}")
                
                # Record failure metrics
                if self.proxy_manager and proxy:
                    self.proxy_manager.record_failure(proxy, time.time() - start_time)
                
                if self.metrics_collector:
                    metric = AccountCreationMetric(
                        timestamp=datetime.now(),
                        platform='email',
                        success=False,
                        error_type=error_msg[:100],  # Truncate long errors
                        proxy_used=proxy,
                        creation_time_seconds=time.time() - start_time
                    )
                    self.metrics_collector.record_account_creation(metric)
                
                if attempt == max_retries - 1:
                    return {'success': False, 'error': error_msg}
                
                # Wait before retry with exponential backoff
                wait_time = (2 ** attempt) + random.uniform(1, 5)
                self.logger.info(f"Waiting {wait_time:.1f}s before retry...")
                await asyncio.sleep(wait_time)
                
            finally:
                # Clean up browser resources
                try:
                    if context:
                        await context.close()
                    if browser:
                        await browser.close()
                    if playwright:
                        await playwright.stop()
                except Exception as cleanup_error:
                    self.logger.error(f"Error during cleanup: {cleanup_error}")
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    async def _setup_page_monitoring(self, page):
        """Set up page monitoring for debugging and analysis"""
        # Log console messages
        page.on('console', lambda msg: self.logger.debug(f"Console: {msg.text}"))
        
        # Log network failures
        page.on('requestfailed', lambda request: 
                self.logger.warning(f"Request failed: {request.url} - {request.failure}"))
        
        # Log responses with errors
        page.on('response', lambda response: 
                self.logger.warning(f"HTTP {response.status}: {response.url}") 
                if response.status >= 400 else None)
    
    async def _fill_registration_form(self, page, identity: Dict[str, Any], provider_config: Dict) -> bool:
        """Fill registration form with human-like behavior"""
        try:
            selectors = provider_config['selectors']
            
            # Fill first name if field exists
            if 'first_name' in selectors:
                if await page.is_visible(selectors['first_name']):
                    await self.browser_automation.human_like_mouse_movement(page, selectors['first_name'])
                    await self.browser_automation.human_like_typing(page, selectors['first_name'], identity['first_name'])
                    await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill last name if field exists
            if 'last_name' in selectors:
                if await page.is_visible(selectors['last_name']):
                    await self.browser_automation.human_like_mouse_movement(page, selectors['last_name'])
                    await self.browser_automation.human_like_typing(page, selectors['last_name'], identity['last_name'])
                    await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill username/email
            if await page.is_visible(selectors['username']):
                await self.browser_automation.human_like_mouse_movement(page, selectors['username'])
                username = identity.get('username', identity['email'].split('@')[0])
                await self.browser_automation.human_like_typing(page, selectors['username'], username)
                await asyncio.sleep(random.uniform(1, 2))
            
            # Fill password
            if await page.is_visible(selectors['password']):
                await self.browser_automation.human_like_mouse_movement(page, selectors['password'])
                await self.browser_automation.human_like_typing(page, selectors['password'], identity['password'])
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Fill confirm password if field exists
            if 'confirm_password' in selectors and await page.is_visible(selectors['confirm_password']):
                await self.browser_automation.human_like_mouse_movement(page, selectors['confirm_password'])
                await self.browser_automation.human_like_typing(page, selectors['confirm_password'], identity['password'])
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Handle additional fields (birth date, phone, etc.)
            await self._fill_additional_fields(page, identity)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error filling registration form: {e}")
            return False
    
    async def _fill_additional_fields(self, page, identity: Dict[str, Any]):
        """Fill additional fields that might appear"""
        # Birth date fields
        birth_year = random.randint(1980, 2000)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        
        # Try common birth date selectors
        birth_selectors = [
            ('select[name="BirthMonth"], select[id="BirthMonth"]', str(birth_month)),
            ('select[name="BirthDay"], select[id="BirthDay"]', str(birth_day)),
            ('select[name="BirthYear"], select[id="BirthYear"]', str(birth_year)),
            ('input[name="birthdate"]', f"{birth_month:02d}/{birth_day:02d}/{birth_year}"),
        ]
        
        for selector, value in birth_selectors:
            try:
                if await page.is_visible(selector):
                    if selector.startswith('select'):
                        await page.select_option(selector, value)
                    else:
                        await self.browser_automation.human_like_typing(page, selector, value)
                    await asyncio.sleep(random.uniform(0.3, 0.8))
            except:
                continue
        
        # Gender selection
        gender_selectors = [
            'select[name="Gender"]',
            'input[name="Gender"][value="M"]',
            'input[name="Gender"][value="F"]'
        ]
        
        for selector in gender_selectors:
            try:
                if await page.is_visible(selector):
                    if selector.startswith('select'):
                        await page.select_option(selector, random.choice(['M', 'F']))
                    else:
                        await page.click(selector)
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    break
            except:
                continue
    
    async def _handle_captcha_comprehensive(self, page, provider_config: Dict) -> Optional[bool]:
        """Handle various types of captchas"""
        try:
            # Check for image captcha
            if 'captcha_image' in provider_config['selectors']:
                captcha_img_selector = provider_config['selectors']['captcha_image']
                if await page.is_visible(captcha_img_selector):
                    return await self._solve_image_captcha(page, provider_config)
            
            # Check for reCAPTCHA
            if await page.is_visible('iframe[src*="recaptcha"]'):
                return await self._solve_recaptcha(page)
            
            # Check for hCaptcha
            if await page.is_visible('iframe[src*="hcaptcha"]'):
                return await self._solve_hcaptcha(page)
            
            # No captcha found
            return None
            
        except Exception as e:
            self.logger.error(f"Error handling captcha: {e}")
            return False
    
    async def _solve_image_captcha(self, page, provider_config: Dict) -> bool:
        """Solve image-based captcha"""
        try:
            captcha_img_selector = provider_config['selectors']['captcha_image']
            captcha_input_selector = provider_config['selectors'].get('captcha_input', 'input[name="captcha"]')
            
            # Take screenshot of captcha
            captcha_element = page.locator(captcha_img_selector).first
            screenshot = await captcha_element.screenshot()
            
            # Solve using captcha service
            result = await self.captcha_solver.solve_captcha(CaptchaType.IMAGE, image_data=screenshot)
            
            if result['success']:
                # Enter solution
                await self.browser_automation.human_like_typing(page, captcha_input_selector, result['solution'])
                await asyncio.sleep(random.uniform(1, 2))
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error solving image captcha: {e}")
            return False
    
    async def _solve_recaptcha(self, page) -> bool:
        """Solve reCAPTCHA"""
        try:
            # Get reCAPTCHA sitekey
            recaptcha_frame = page.frame_locator('iframe[src*="recaptcha"]')
            sitekey = await page.get_attribute('div[data-sitekey]', 'data-sitekey')
            
            if not sitekey:
                return False
            
            # Solve using captcha service
            result = await self.captcha_solver.solve_captcha(
                CaptchaType.RECAPTCHA_V2,
                sitekey=sitekey,
                page_url=page.url
            )
            
            if result['success']:
                # Inject solution
                await page.evaluate(f'''
                    document.getElementById("g-recaptcha-response").innerHTML = "{result['solution']}";
                    if (typeof grecaptcha !== 'undefined') {{
                        grecaptcha.getResponse = function() {{ return "{result['solution']}"; }};
                    }}
                ''')
                await asyncio.sleep(random.uniform(1, 2))
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error solving reCAPTCHA: {e}")
            return False
    
    async def _solve_hcaptcha(self, page) -> bool:
        """Solve hCaptcha"""
        try:
            # Get hCaptcha sitekey
            sitekey = await page.get_attribute('div[data-sitekey]', 'data-sitekey')
            
            if not sitekey:
                return False
            
            # Solve using captcha service
            result = await self.captcha_solver.solve_captcha(
                CaptchaType.HCAPTCHA,
                sitekey=sitekey,
                page_url=page.url
            )
            
            if result['success']:
                # Inject solution
                await page.evaluate(f'''
                    document.querySelector("[name=h-captcha-response]").value = "{result['solution']}";
                ''')
                await asyncio.sleep(random.uniform(1, 2))
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error solving hCaptcha: {e}")
            return False
    
    async def _submit_form_human_like(self, page, provider_config: Dict):
        """Submit form with human-like behavior"""
        selectors = provider_config['selectors']
        
        # Try different submit methods
        submit_selectors = [
            selectors.get('submit'),
            selectors.get('next'),
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Create")',
            'button:has-text("Sign up")',
            'button:has-text("Next")'
        ]
        
        for selector in submit_selectors:
            if not selector:
                continue
                
            try:
                if await page.is_visible(selector):
                    # Move mouse to button and pause (like reading)
                    await self.browser_automation.human_like_mouse_movement(page, selector)
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    # Click submit
                    await page.click(selector)
                    await asyncio.sleep(random.uniform(2, 4))
                    return
            except:
                continue
        
        # Fallback: try pressing Enter
        await page.keyboard.press('Enter')
        await asyncio.sleep(random.uniform(2, 4))
    
    async def _check_registration_result(self, page, provider_config: Dict, identity: Dict[str, Any]) -> Dict[str, Any]:
        """Check registration result and handle various outcomes"""
        try:
            # Wait for page to load
            await page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check for success indicators
            for indicator in provider_config['success_indicators']:
                if await page.is_visible(indicator):
                    return {
                        'success': True,
                        'email': identity['email'],
                        'password': identity['password'],
                        'status': 'created',
                        'message': 'Account created successfully'
                    }
            
            # Check for error indicators
            for indicator in provider_config['error_indicators']:
                if await page.is_visible(indicator):
                    error_text = await page.text_content(indicator)
                    return {
                        'success': False,
                        'error': f'Registration error: {error_text}',
                        'retry_recommended': 'username' in error_text.lower()
                    }
            
            # Check for phone verification requirement
            phone_indicators = [
                'text=phone number',
                'text=mobile number',
                'text=verify your phone',
                'input[type="tel"]'
            ]
            
            for indicator in phone_indicators:
                if await page.is_visible(indicator):
                    return {
                        'success': True,
                        'email': identity['email'],
                        'password': identity['password'],
                        'status': 'needs_phone_verification',
                        'message': 'Account created but requires phone verification'
                    }
            
            # Check current URL for clues
            current_url = page.url
            if 'welcome' in current_url.lower() or 'success' in current_url.lower():
                return {
                    'success': True,
                    'email': identity['email'],
                    'password': identity['password'],
                    'status': 'created',
                    'message': 'Account created successfully (URL indicates success)'
                }
            
            # Default: assume failure if we can't determine success
            page_content = await page.content()
            return {
                'success': False,
                'error': 'Could not determine registration result',
                'page_url': current_url,
                'page_title': await page.title()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error checking registration result: {str(e)}'
            }