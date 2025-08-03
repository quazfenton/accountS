import asyncio
import random
import time
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from utils.stealth_browser import StealthBrowserAutomation
from utils.advanced_captcha_solver import AdvancedCaptchaSolver, CaptchaType

class VerificationType(Enum):
    SMS = "sms"
    EMAIL = "email"
    VOICE = "voice"
    CAPTCHA_IMAGE = "captcha_image"
    RECAPTCHA = "recaptcha"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    PHONE_VERIFICATION = "phone_verification"
    TWO_FACTOR = "two_factor"

@dataclass
class VerificationContext:
    verification_type: VerificationType
    platform: str
    page_url: str
    element_selectors: Dict[str, str]
    metadata: Dict[str, Any]
    timeout: int = 300
    max_attempts: int = 3

class AdvancedVerificationSolver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.browser_automation = StealthBrowserAutomation()
        self.captcha_solver = AdvancedCaptchaSolver()
        
        # SMS service configurations
        self.sms_services = {
            'primary': {
                'url': 'https://api.sms-service.com/v1',
                'api_key': None,  # Will be loaded from config
                'supported_countries': ['US', 'UK', 'CA', 'AU']
            },
            'fallback': {
                'url': 'https://api.backup-sms.com/v2',
                'api_key': None,
                'supported_countries': ['US', 'UK']
            }
        }
        
        # Voice verification services
        self.voice_services = {
            'primary': {
                'url': 'https://api.voice-verify.com/v1',
                'api_key': None
            }
        }
        
        # Human intervention thresholds
        self.intervention_thresholds = {
            'consecutive_failures': 3,
            'captcha_solve_failures': 2,
            'sms_timeout_count': 2
        }
        
        # Failure tracking
        self.failure_counts = {
            'consecutive_failures': 0,
            'captcha_failures': 0,
            'sms_timeouts': 0
        }
    
    async def solve_verification(self, context: VerificationContext, page) -> Dict[str, Any]:
        """Main verification solving method with strategy selection"""
        try:
            self.logger.info(f"Solving {context.verification_type.value} verification for {context.platform}")
            
            # Check if human intervention is needed
            if self._should_request_human_intervention():
                return await self._request_human_intervention(context)
            
            # Select optimal strategy based on verification type
            strategy = self._select_optimal_strategy(context)
            
            # Execute strategy with retries
            for attempt in range(context.max_attempts):
                try:
                    result = await strategy(context, page, attempt + 1)
                    
                    if result['success']:
                        self._reset_failure_counts()
                        return result
                    else:
                        self.logger.warning(f"Verification attempt {attempt + 1} failed: {result.get('error', 'Unknown error')}")
                        
                        if attempt < context.max_attempts - 1:
                            wait_time = (2 ** attempt) + random.uniform(1, 3)
                            await asyncio.sleep(wait_time)
                
                except Exception as e:
                    self.logger.error(f"Verification attempt {attempt + 1} error: {e}")
                    if attempt < context.max_attempts - 1:
                        await asyncio.sleep(random.uniform(2, 5))
            
            # All attempts failed
            self._increment_failure_count('consecutive_failures')
            return {
                'success': False,
                'error': f'All {context.max_attempts} verification attempts failed',
                'requires_human_intervention': self._should_request_human_intervention()
            }
            
        except Exception as e:
            self.logger.error(f"Critical error in verification solver: {e}")
            return {'success': False, 'error': str(e)}
    
    def _select_optimal_strategy(self, context: VerificationContext):
        """Select the best strategy for the given verification type"""
        strategy_map = {
            VerificationType.SMS: self._solve_sms_verification,
            VerificationType.EMAIL: self._solve_email_verification,
            VerificationType.VOICE: self._solve_voice_verification,
            VerificationType.CAPTCHA_IMAGE: self._solve_image_captcha,
            VerificationType.RECAPTCHA: self._solve_recaptcha,
            VerificationType.HCAPTCHA: self._solve_hcaptcha,
            VerificationType.FUNCAPTCHA: self._solve_funcaptcha,
            VerificationType.PHONE_VERIFICATION: self._solve_phone_verification,
            VerificationType.TWO_FACTOR: self._solve_two_factor
        }
        
        return strategy_map.get(context.verification_type, self._solve_generic_verification)
    
    async def _solve_sms_verification(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve SMS verification with intelligent phone number management"""
        try:
            # Get phone number from SMS service
            phone_result = await self._get_phone_number(context.platform)
            if not phone_result['success']:
                return phone_result
            
            phone_number = phone_result['phone_number']
            service_id = phone_result['service_id']
            
            # Enter phone number
            phone_input_selector = context.element_selectors.get('phone_input', 'input[type="tel"], input[name="phone"]')
            if await page.is_visible(phone_input_selector):
                await self.browser_automation.human_like_typing(page, phone_input_selector, phone_number)
                await asyncio.sleep(random.uniform(1, 2))
            
            # Click send SMS button
            send_button_selector = context.element_selectors.get('send_button', 'button:has-text("Send"), button:has-text("Verify")')
            if await page.is_visible(send_button_selector):
                await page.click(send_button_selector)
                await asyncio.sleep(random.uniform(2, 4))
            
            # Wait for SMS and enter code
            sms_result = await self._wait_for_sms_code(service_id, context.timeout)
            if not sms_result['success']:
                self._increment_failure_count('sms_timeouts')
                return sms_result
            
            # Enter SMS code
            code_input_selector = context.element_selectors.get('code_input', 'input[name="code"], input[placeholder*="code"]')
            if await page.is_visible(code_input_selector):
                await self.browser_automation.human_like_typing(page, code_input_selector, sms_result['code'])
                await asyncio.sleep(random.uniform(1, 2))
            
            # Submit code
            submit_selector = context.element_selectors.get('submit_button', 'button[type="submit"], button:has-text("Verify")')
            if await page.is_visible(submit_selector):
                await page.click(submit_selector)
                await asyncio.sleep(random.uniform(2, 4))
            
            # Check if verification was successful
            success_indicators = context.metadata.get('success_indicators', ['text=Success', 'text=Verified'])
            for indicator in success_indicators:
                if await page.is_visible(indicator):
                    return {
                        'success': True,
                        'method': 'sms',
                        'phone_number': phone_number,
                        'verification_code': sms_result['code']
                    }
            
            return {'success': False, 'error': 'SMS verification failed - no success indicator found'}
            
        except Exception as e:
            return {'success': False, 'error': f'SMS verification error: {str(e)}'}
    
    async def _solve_email_verification(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve email verification"""
        try:
            # Check if email verification link was clicked automatically
            # or if we need to enter a code from email
            
            code_input_selector = context.element_selectors.get('code_input', 'input[name="code"], input[placeholder*="code"]')
            
            if await page.is_visible(code_input_selector):
                # Need to get code from email
                email_result = await self._get_email_verification_code(context.metadata.get('email'))
                if not email_result['success']:
                    return email_result
                
                await self.browser_automation.human_like_typing(page, code_input_selector, email_result['code'])
                
                submit_selector = context.element_selectors.get('submit_button', 'button[type="submit"]')
                if await page.is_visible(submit_selector):
                    await page.click(submit_selector)
                    await asyncio.sleep(random.uniform(2, 4))
            
            # Check for success
            success_indicators = context.metadata.get('success_indicators', ['text=Verified'])
            for indicator in success_indicators:
                if await page.is_visible(indicator):
                    return {'success': True, 'method': 'email'}
            
            return {'success': False, 'error': 'Email verification failed'}
            
        except Exception as e:
            return {'success': False, 'error': f'Email verification error: {str(e)}'}
    
    async def _solve_voice_verification(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve voice verification"""
        try:
            # Get phone number for voice call
            phone_result = await self._get_phone_number(context.platform, prefer_voice=True)
            if not phone_result['success']:
                return phone_result
            
            phone_number = phone_result['phone_number']
            
            # Enter phone number
            phone_input_selector = context.element_selectors.get('phone_input', 'input[type="tel"]')
            if await page.is_visible(phone_input_selector):
                await self.browser_automation.human_like_typing(page, phone_input_selector, phone_number)
            
            # Click call button
            call_button_selector = context.element_selectors.get('call_button', 'button:has-text("Call")')
            if await page.is_visible(call_button_selector):
                await page.click(call_button_selector)
                await asyncio.sleep(random.uniform(3, 6))
            
            # Wait for voice call and get code
            voice_result = await self._wait_for_voice_code(phone_result['service_id'], context.timeout)
            if not voice_result['success']:
                return voice_result
            
            # Enter voice code
            code_input_selector = context.element_selectors.get('code_input', 'input[name="code"]')
            if await page.is_visible(code_input_selector):
                await self.browser_automation.human_like_typing(page, code_input_selector, voice_result['code'])
            
            return {'success': True, 'method': 'voice', 'phone_number': phone_number}
            
        except Exception as e:
            return {'success': False, 'error': f'Voice verification error: {str(e)}'}
    
    async def _solve_image_captcha(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve image captcha"""
        try:
            captcha_img_selector = context.element_selectors.get('captcha_image', 'img[src*="captcha"]')
            captcha_input_selector = context.element_selectors.get('captcha_input', 'input[name="captcha"]')
            
            if not await page.is_visible(captcha_img_selector):
                return {'success': False, 'error': 'Captcha image not found'}
            
            # Take screenshot of captcha
            captcha_element = page.locator(captcha_img_selector).first
            screenshot = await captcha_element.screenshot()
            
            # Solve captcha
            result = await self.captcha_solver.solve_captcha(CaptchaType.IMAGE, image_data=screenshot)
            
            if result['success']:
                await self.browser_automation.human_like_typing(page, captcha_input_selector, result['solution'])
                return {'success': True, 'method': 'image_captcha', 'solution': result['solution']}
            else:
                self._increment_failure_count('captcha_failures')
                return {'success': False, 'error': 'Failed to solve image captcha'}
                
        except Exception as e:
            self._increment_failure_count('captcha_failures')
            return {'success': False, 'error': f'Image captcha error: {str(e)}'}
    
    async def _solve_recaptcha(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve reCAPTCHA"""
        try:
            # Get sitekey
            sitekey = await page.get_attribute('div[data-sitekey]', 'data-sitekey')
            if not sitekey:
                return {'success': False, 'error': 'reCAPTCHA sitekey not found'}
            
            # Solve reCAPTCHA
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
                return {'success': True, 'method': 'recaptcha'}
            else:
                self._increment_failure_count('captcha_failures')
                return {'success': False, 'error': 'Failed to solve reCAPTCHA'}
                
        except Exception as e:
            self._increment_failure_count('captcha_failures')
            return {'success': False, 'error': f'reCAPTCHA error: {str(e)}'}
    
    async def _solve_hcaptcha(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve hCaptcha"""
        try:
            # Get sitekey
            sitekey = await page.get_attribute('div[data-sitekey]', 'data-sitekey')
            if not sitekey:
                return {'success': False, 'error': 'hCaptcha sitekey not found'}
            
            # Solve hCaptcha
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
                return {'success': True, 'method': 'hcaptcha'}
            else:
                self._increment_failure_count('captcha_failures')
                return {'success': False, 'error': 'Failed to solve hCaptcha'}
                
        except Exception as e:
            self._increment_failure_count('captcha_failures')
            return {'success': False, 'error': f'hCaptcha error: {str(e)}'}
    
    async def _solve_funcaptcha(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve FunCaptcha"""
        try:
            # FunCaptcha implementation would go here
            return {'success': False, 'error': 'FunCaptcha solver not implemented yet'}
        except Exception as e:
            return {'success': False, 'error': f'FunCaptcha error: {str(e)}'}
    
    async def _solve_phone_verification(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve general phone verification"""
        # This can route to SMS or voice based on available options
        if await page.is_visible('button:has-text("Text"), button:has-text("SMS")'):
            context.verification_type = VerificationType.SMS
            return await self._solve_sms_verification(context, page, attempt)
        elif await page.is_visible('button:has-text("Call"), button:has-text("Voice")'):
            context.verification_type = VerificationType.VOICE
            return await self._solve_voice_verification(context, page, attempt)
        else:
            return {'success': False, 'error': 'No phone verification method available'}
    
    async def _solve_two_factor(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Solve two-factor authentication"""
        try:
            # This would integrate with authenticator apps or backup codes
            return {'success': False, 'error': '2FA solver not implemented - requires human intervention'}
        except Exception as e:
            return {'success': False, 'error': f'2FA error: {str(e)}'}
    
    async def _solve_generic_verification(self, context: VerificationContext, page, attempt: int) -> Dict[str, Any]:
        """Generic verification solver for unknown types"""
        return {'success': False, 'error': f'Unknown verification type: {context.verification_type}'}
    
    async def _get_phone_number(self, platform: str, prefer_voice: bool = False) -> Dict[str, Any]:
        """Get phone number from SMS/voice service"""
        try:
            # Try primary service first
            for service_name, service_config in self.sms_services.items():
                if not service_config['api_key']:
                    continue
                
                response = requests.post(
                    f"{service_config['url']}/get-number",
                    json={
                        'api_key': service_config['api_key'],
                        'service': platform,
                        'country': 'US',
                        'voice_preferred': prefer_voice
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'success': True,
                        'phone_number': data['phone_number'],
                        'service_id': data['service_id'],
                        'service_name': service_name
                    }
            
            return {'success': False, 'error': 'No SMS services available'}
            
        except Exception as e:
            return {'success': False, 'error': f'Error getting phone number: {str(e)}'}
    
    async def _wait_for_sms_code(self, service_id: str, timeout: int) -> Dict[str, Any]:
        """Wait for SMS code from service"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Check for SMS code
                for service_name, service_config in self.sms_services.items():
                    if not service_config['api_key']:
                        continue
                    
                    try:
                        response = requests.get(
                            f"{service_config['url']}/get-sms",
                            params={
                                'api_key': service_config['api_key'],
                                'service_id': service_id
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('status') == 'received':
                                return {
                                    'success': True,
                                    'code': data['code'],
                                    'message': data.get('message', '')
                                }
                    except:
                        continue
                
                await asyncio.sleep(5)  # Check every 5 seconds
            
            return {'success': False, 'error': 'SMS timeout - no code received'}
            
        except Exception as e:
            return {'success': False, 'error': f'Error waiting for SMS: {str(e)}'}
    
    async def _wait_for_voice_code(self, service_id: str, timeout: int) -> Dict[str, Any]:
        """Wait for voice verification code"""
        # Similar to SMS but for voice calls
        return {'success': False, 'error': 'Voice verification not implemented yet'}
    
    async def _get_email_verification_code(self, email: str) -> Dict[str, Any]:
        """Get verification code from email"""
        # This would integrate with email services to read verification emails
        return {'success': False, 'error': 'Email code extraction not implemented yet'}
    
    def _should_request_human_intervention(self) -> bool:
        """Check if human intervention should be requested"""
        return (
            self.failure_counts['consecutive_failures'] >= self.intervention_thresholds['consecutive_failures'] or
            self.failure_counts['captcha_failures'] >= self.intervention_thresholds['captcha_solve_failures'] or
            self.failure_counts['sms_timeouts'] >= self.intervention_thresholds['sms_timeout_count']
        )
    
    async def _request_human_intervention(self, context: VerificationContext) -> Dict[str, Any]:
        """Request human intervention"""
        self.logger.critical(f"Human intervention required for {context.verification_type.value} verification")
        
        # Send notification
        try:
            from utils.notifier import Notifier
            notifier = Notifier()
            notifier.human_intervention_required(
                context.platform,
                f"Verification solver needs help with {context.verification_type.value}",
                {'page_url': context.page_url, 'failure_counts': self.failure_counts}
            )
        except Exception as e:
            self.logger.error(f"Failed to send intervention notification: {e}")
        
        return {
            'success': False,
            'error': 'Human intervention required',
            'requires_human_intervention': True,
            'intervention_reason': f'Too many failures: {self.failure_counts}'
        }
    
    def _increment_failure_count(self, failure_type: str):
        """Increment failure count for tracking"""
        if failure_type in self.failure_counts:
            self.failure_counts[failure_type] += 1
    
    def _reset_failure_counts(self):
        """Reset failure counts after successful verification"""
        self.failure_counts = {key: 0 for key in self.failure_counts}