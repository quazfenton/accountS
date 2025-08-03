import random
import time
import numpy as np
import tempfile
import requests
import re
import math
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, BrowserContext
from modules.browserless import Browserless
from config.config import Config
from .detection_prevention import DetectionPrevention
from utils.notifier import Notifier
from faker import Faker

class SocialMediaRegistration:
    def __init__(self, email, password, proxy=None):
        self.config = Config()
        self.email = email
        self.password = password
        self.proxy = proxy
        self.browser = None
        self.page = None
        self.fake = Faker()
        self.behavior_profile = self._generate_behavior_profile()
        self.notifier = Notifier() # Initialize Notifier
        self.browserless_client = Browserless() # Initialize Browserless client
        
    def _generate_behavior_profile(self):
        """Generate unique behavior fingerprint for each session"""
        return {
            'typing_speed': random.uniform(0.05, 0.2),
            'mouse_speed': random.uniform(3, 8),
            'scroll_speed': random.uniform(1, 5),
            'error_rate': random.uniform(0.01, 0.1),
            'pause_frequency': random.randint(2, 5),
            'browser_viewport': {
                'width': random.choice([1366, 1920, 1440, 1536]),
                'height': random.choice([768, 1080, 900, 864])
            }
        }
    
    def _human_type(self, selector, text):
        """Simulate human typing with errors and corrections"""
        self.page.click(selector)
        for i, char in enumerate(text):
            # Random pause between keystrokes
            if random.random() < 0.3:
                time.sleep(random.uniform(0.1, 0.5))
            
            # Simulate typo with correction
            if random.random() < self.behavior_profile['error_rate'] and i > 3:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz1234567890')
                self.page.keyboard.press(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                self.page.keyboard.press('Backspace')
            
            self.page.keyboard.press(char)
            time.sleep(self.behavior_profile['typing_speed'])
    
    def _human_mouse_move(self, selector):
        """Simulate human-like mouse movement to element"""
        element = self.page.locator(selector)
        box = element.bounding_box()
        
        if not box:
            return
            
        target_x = box['x'] + box['width']/2
        target_y = box['y'] + box['height']/2
        
        # Generate random path using Bezier curve
        current_x, current_y = 0, 0
        steps = 20
        for i in range(steps):
            t = i / steps
            # Cubic Bezier with random control points
            x = math.floor((1-t)**3 * current_x + 3*(1-t)**2*t*random.randint(0,1000) + 3*(1-t)*t**2*random.randint(0,1000) + t**3*target_x)
            y = math.floor((1-t)**3 * current_y + 3*(1-t)**2*t*random.randint(0,1000) + 3*(1-t)*t**2*random.randint(0,1000) + t**3*target_y)
            
            self.page.mouse.move(x, y)
            current_x, current_y = x, y
            time.sleep(self.behavior_profile['mouse_speed']/1000)
    
    def init_browser(self):
        """Initialize Playwright browser with advanced fingerprint spoofing"""
        self.playwright = sync_playwright().start()
        
        proxy_settings = {
            'server': f'http://{self.proxy}'
        } if self.proxy else None
        
        self.browser = self.playwright.chromium.launch(
            headless=False,
            proxy=proxy_settings,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                f'--window-size={self.behavior_profile["browser_viewport"]["width"]},{self.behavior_profile["browser_viewport"]["height"]}'
            ]
        )
        
        # Create new context with advanced fingerprint spoofing
        context = self.browser.new_context(
            viewport=self.behavior_profile["browser_viewport"],
            user_agent=self.fake.user_agent(),
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'longitude': -74.006, 'latitude': 40.7128},
            permissions=['geolocation']
        )
        
        # Apply advanced detection prevention
        dp = DetectionPrevention(context)
        dp.apply_stealth()
        
        # Override navigator properties
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
        """)
        
        self.page = context.new_page()
    
    def _ai_behavior_randomization(self):
        """Randomize behavior patterns using ML-generated sequences"""
        # Random browsing pattern before registration
        actions = [
            ('scroll', random.randint(200, 800)),
            ('move', random.randint(-100, 100), random.randint(-100, 100)),
            ('wait', random.uniform(0.5, 2))
        ]
        
        # Execute random actions
        for action in actions:
            if action[0] == 'scroll':
                self.page.mouse.wheel(0, action[1])
            elif action[0] == 'move':
                self.page.mouse.move(action[1], action[2])
            elif action[0] == 'wait':
                time.sleep(action[1])
    
    def close_browser(self):
        """Close browser instance"""
        if hasattr(self, 'browser') and self.browser:
            self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            self.playwright.stop()
    
    def register_twitter(self, identity=None, profile=None):
        """Register Twitter account with advanced human-like interactions"""
        try:
            self.init_browser()
            self.page.goto('https://twitter.com/i/flow/signup')
            self._ai_behavior_randomization()
            
            # Use profile if provided
            if profile:
                first_name = profile['personal'].get('first_name', profile['basic']['first_name'])
                last_name = profile['personal'].get('last_name', '')
            else:
                first_name = identity['first_name']
                last_name = identity.get('last_name', '')
            
            # Fill form with human-like interactions
            self._human_mouse_move('input[name="name"]')
            self._human_type('input[name="name"]', f"{first_name} {last_name}")
            
            # Continue to next step
            self._human_mouse_move('div[role="button"][aria-label="Next"]')
            self.page.click('div[role="button"][aria-label="Next"]')
            time.sleep(random.uniform(1, 2))
            
            # Fill email
            self._human_mouse_move('input[autocomplete="email"]')
            self._human_type('input[autocomplete="email"]', self.email)
            
            # Select birth month
            self.page.select_option('select[aria-label="Month"]', value=str(random.randint(1, 12)))
            time.sleep(random.uniform(0.5, 1))
            
            # Select birth day
            self.page.select_option('select[aria-label="Day"]', value=str(random.randint(1, 28)))
            time.sleep(random.uniform(0.5, 1))
            
            # Select birth year
            min_year = datetime.now().year - 65
            max_year = datetime.now().year - 18
            birth_year = str(random.randint(min_year, max_year))
            self.page.select_option('select[aria-label="Year"]', value=birth_year)
            time.sleep(random.uniform(0.5, 1))
            
            # Continue to next step
            self._human_mouse_move('div[role="button"][aria-label="Next"]')
            self.page.click('div[role="button"][aria-label="Next"]')
            time.sleep(random.uniform(1, 2))
            
            # Handle signup method (email or phone)
            if self.page.is_visible('text=Use email instead?'):
                self.page.click('text=Use email instead?')
                time.sleep(random.uniform(1, 2))
            
            # Submit registration
            self._human_mouse_move('div[role="button"][data-testid="ocfSignupReviewButton"]')
            self.page.click('div[role="button"][data-testid="ocfSignupReviewButton"]')
            time.sleep(random.uniform(3, 5))
            
            # Handle verification requirements
            if self.page.is_visible('text=Verify your phone number') or self.page.is_visible('text=Solve this puzzle'):
                verification_result = self.handle_verification('twitter')
                if verification_result['status'] != 'success':
                    return verification_result
            
            # Handle confirmation screen
            if self.page.is_visible('text=Confirm your email'):
                self._human_mouse_move('input[type="text"]')
                self._human_type('input[type="text"]', self.email)
                self.page.click('div[role="button"][data-testid="ocfEnterTextNextButton"]')
                time.sleep(random.uniform(3, 5))
            
            # Extract username
            username_element = self.page.query_selector('div[data-testid="UserName"]')
            username = username_element.inner_text().split('@')[1] if username_element else f"{first_name}_{last_name}"
            
            return {
                'platform': 'twitter',
                'username': username,
                'email': self.email,
                'status': 'success'
            }
        except Exception as e:
            return {
                'platform': 'twitter',
                'error': str(e),
                'status': 'failed'
            }
        finally:
            self.close_browser()
    
    def register_facebook(self, identity=None):
        """Register Facebook account using Playwright automation"""
        try:
            self.init_browser()
            self.page.goto('https://www.facebook.com/r.php')
            
            # Use identity if provided, otherwise generate from email
            if not identity:
                identity = {
                    'first_name': self.email.split('@')[0],
                    'last_name': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))
                }
            
            # Fill registration form
            self.page.fill('input[name="firstname"]', identity['first_name'])
            self.page.fill('input[name="lastname"]', identity['last_name'])
            self.page.fill('input[name="reg_email__"]', self.email)
            self.page.fill('input[name="reg_email_confirmation__"]', self.email)
            self.page.fill('input[name="reg_passwd__"]', self.password)
            
            # Select birth date
            birth_day = random.randint(1, 28)
            birth_month = random.randint(1, 12)
            birth_year = random.randint(1980, 2000)

            self.page.select_option('select[name="birthday_day"]', value=str(birth_day))
            self.page.select_option('select[name="birthday_month"]', value=str(birth_month))
            self.page.select_option('select[name="birthday_year"]', value=str(birth_year))
            
            # Select gender
            gender = random.choice(['male', 'female', 'custom'])
            self.page.click(f'input[name="sex"][value="{random.randint(1,3)}"]')
            
            # Submit form
            self.page.click('button[name="websubmit"]')
            time.sleep(5)
            
            # Handle verification
            if self.page.is_visible('text=Confirm Your Email'):
                return self.handle_verification('facebook')
            
            return {
                'platform': 'facebook',
                'email': self.email,
                'status': 'success'
            }
        except Exception as e:
            return {
                'platform': 'facebook',
                'error': str(e),
                'status': 'failed'
            }
        finally:
            self.close_browser()
    
    def handle_verification(self, platform):
        """Handle verification requirements (captcha, SMS, etc.)"""
        try:
            if platform == 'twitter':
                # Twitter-specific verification handling
                if self.page.is_visible('text=Verify your phone number'):
                    return self.handle_sms_verification()
                elif self.page.is_visible('text=Solve this puzzle'):
                    return self.handle_captcha()
            elif platform == 'facebook':
                # Facebook-specific verification handling
                if self.page.is_visible('text=Enter Code to Continue'):
                    return self.handle_sms_verification()
            
            # Handle other platforms
            if self.page.is_visible('text=Verify your email'):
                # Email verification
                return {'status': 'email_verification_sent', 'platform': platform}
            elif self.page.is_visible('text=Verify your phone'):
                return self.handle_sms_verification()
            elif self.page.is_visible('text=Solve this puzzle') or self.page.is_visible('id=captcha'):
                return self.handle_captcha()
            
            return {'status': 'verification_required', 'platform': platform}
        except Exception as e:
            return {'status': 'verification_failed', 'error': str(e), 'platform': platform}
    
    def handle_captcha(self):
        """Solve captcha challenges with improved reliability"""
        try:
            # Check for different captcha types
            if self.page.is_visible('iframe[title*="recaptcha"]'):
                # Google reCAPTCHA
                return self.solve_recaptcha()
            elif self.page.is_visible('img.captcha-image'):
                # Image-based captcha
                return self.solve_image_captcha()
            elif self.page.is_visible('div#hcaptcha'):
                # hCaptcha - similar to reCAPTCHA
                return self.solve_hcaptcha()
            else:
                print("Unknown captcha type detected")
                return {'status': 'captcha_failed', 'reason': 'unknown_type'}
        except Exception as e:
            print(f"Captcha handling error: {str(e)}")
            return {'status': 'captcha_failed', 'error': str(e)}
    
    def solve_image_captcha(self):
        """Solve traditional image-based captchas"""
        try:
            # Get captcha image
            captcha_img = self.page.query_selector('img.captcha-image')
            if captcha_img:
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                    captcha_img.screenshot(path=tmpfile.name)
                    tmpfile.flush()
                    
                    # Use external service to solve captcha
                    with open(tmpfile.name, 'rb') as f:
                        response = requests.post(
                            self.config.CAPTCHA_SERVICE_URL,
                            files={'image': f},
                            data={'api_key': self.config.CAPTCHA_API_KEY},
                            timeout=60
                        )
                    
                    if response.status_code == 200:
                        solution = response.json().get('solution')
                        if solution:
                            # Find input field and enter solution
                            input_selector = 'input.captcha-input, input#captcha'
                            self.page.fill(input_selector, solution)
                            self.page.click('button:has-text("Verify"), button#captcha-submit')
                            time.sleep(2)
                            return {'status': 'captcha_solved'}
        except Exception as e:
            print(f"Image captcha solving failed: {str(e)}")
        
        return {'status': 'captcha_failed'}
    
    def solve_recaptcha(self):
        """Solve Google reCAPTCHA using external service"""
        try:
            # Extract sitekey from iframe
            recaptcha_frame = self.page.query_selector('iframe[title*="recaptcha"]')
            sitekey = recaptcha_frame.get_attribute('src').split('k=')[1].split('&')[0]
            
            # Get page URL
            page_url = self.page.url
            
            # Solve using external service
            response = requests.post(
                f"{self.config.CAPTCHA_SERVICE_URL}/recaptcha",
                json={
                    "api_key": self.config.CAPTCHA_API_KEY,
                    "sitekey": sitekey,
                    "url": page_url
                },
                timeout=120
            )
            
            if response.status_code == 200:
                solution = response.json().get('solution')
                if solution:
                    # Inject solution into page
                    self.page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML = "{solution}";')
                    self.page.evaluate('document.getElementById("recaptcha-token").value = arguments[0];', solution)
                    time.sleep(1)
                    self.page.click('button:has-text("Verify")')
                    time.sleep(2)
                    return {'status': 'captcha_solved'}
        except Exception as e:
            print(f"reCAPTCHA solving failed: {str(e)}")
        
        return {'status': 'captcha_failed'}
    
    def solve_hcaptcha(self):
        """Solve hCaptcha using external service"""
        try:
            # Extract sitekey from hCaptcha div
            hcaptcha_div = self.page.query_selector('div[data-sitekey]')
            if not hcaptcha_div:
                return {'status': 'captcha_failed', 'reason': 'no_sitekey'}
                
            sitekey = hcaptcha_div.get_attribute('data-sitekey')
            page_url = self.page.url
            
            # Solve using external service
            response = requests.post(
                f"{self.config.CAPTCHA_SERVICE_URL}/hcaptcha",
                json={
                    "api_key": self.config.CAPTCHA_API_KEY,
                    "sitekey": sitekey,
                    "url": page_url
                },
                timeout=120
            )
            
            if response.status_code == 200:
                solution = response.json().get('solution')
                if solution:
                    # Inject solution into page
                    self.page.evaluate(f'document.querySelector("[name=h-captcha-response]").value = "{solution}";')
                    time.sleep(1)
                    self.page.click('button:has-text("Verify")')
                    time.sleep(2)
                    return {'status': 'captcha_solved'}
        except Exception as e:
            print(f"hCaptcha solving failed: {str(e)}")
        
        return {'status': 'captcha_failed'}
    
    def handle_sms_verification(self, platform='twitter'):
        """Handle SMS verification using SIP service with improved reliability"""
        try:
            # Use SMS service to get phone number
            if not self.config.SMS_SERVICE_URL:
                return {'status': 'sms_failed', 'reason': 'sms_service_not_configured'}
                
            response = requests.post(
                self.config.SMS_SERVICE_URL,
                json={
                    'api_key': self.config.SMS_API_KEY,
                    'service': platform
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return {'status': 'sms_failed', 'reason': 'number_request_failed'}
                
            phone_data = response.json()
            phone_number = phone_data.get('number')
            if not phone_number:
                return {'status': 'sms_failed', 'reason': 'no_number'}
            
            # Fill phone number on page
            phone_input_selector = 'input[name="phone_number"], input[type="tel"]'
            self.page.fill(phone_input_selector, phone_number)
            
            # Click send code button
            send_button_selector = 'button:has-text("Send code"), button:has-text("Send SMS")'
            self.page.click(send_button_selector)
            
            # Wait for SMS to arrive with exponential backoff
            code = None
            for attempt in range(1, 6):
                time.sleep(5 * attempt)  # 5, 10, 15, 20, 25 seconds
                
                # Check for code
                code_response = requests.get(
                    f"{self.config.SMS_SERVICE_URL}/code",
                    params={
                        'number': phone_number,
                        'api_key': self.config.SMS_API_KEY
                    },
                    timeout=30
                )
                
                if code_response.status_code == 200:
                    code_data = code_response.json()
                    code = code_data.get('code')
                    if code:
                        break
            
            if not code:
                return {'status': 'sms_failed', 'reason': 'no_code_received'}
            
            # Enter verification code
            code_input_selector = 'input[name="verification_code"], input[type="text"][inputmode="numeric"]'
            self.page.fill(code_input_selector, code)
            
            # Submit verification
            verify_button_selector = 'button:has-text("Verify"), button:has-text("Submit")'
            self.page.click(verify_button_selector)
            time.sleep(3)
            
            return {'status': 'sms_verified'}
        except Exception as e:
            print(f"SMS verification failed: {str(e)}")
            return {'status': 'sms_failed', 'error': str(e)}

    def register_instagram(self, identity=None, profile=None):
        """Register Instagram account with profile picture and advanced interactions"""
        try:
            self.init_browser()
            self.page.goto('https://www.instagram.com/accounts/emailsignup/')
            self._ai_behavior_randomization()
            
            # Use profile if provided
            if profile:
                first_name = profile['personal'].get('first_name', profile['basic']['first_name'])
                last_name = profile['personal'].get('last_name', '')
                profile_picture_path = profile['media'].get('profile_picture_path')
            else:
                first_name = identity['first_name']
                last_name = identity.get('last_name', '')
                profile_picture_path = None # No profile picture if no full profile
            
            # Fill email and name
            self._human_mouse_move('input[name="emailOrPhone"]')
            self._human_type('input[name="emailOrPhone"]', self.email)
            
            self._human_mouse_move('input[name="fullName"]')
            self._human_type('input[name="fullName"]', f"{first_name} {last_name}")
            
            # Fill username
            username = f"{first_name}_{last_name}_{random.randint(100,999)}"
            self._human_mouse_move('input[name="username"]')
            self._human_type('input[name="username"]', username)
            
            # Fill password
            self._human_mouse_move('input[name="password"]')
            self._human_type('input[name="password"]', self.password)
            
            # Submit form
            self._human_mouse_move('button[type="submit"]')
            self.page.click('button[type="submit"]')
            time.sleep(random.uniform(3, 5))
            
            # Handle birthdate screen
            if self.page.is_visible('select[title="Month:"]'):
                # Select birth month
                self.page.select_option('select[title="Month:"]', value=str(random.randint(1, 12)))
                time.sleep(random.uniform(0.5, 1))
                
                # Select birth day
                self.page.select_option('select[title="Day:"]', value=str(random.randint(1, 28)))
                time.sleep(random.uniform(0.5, 1))
                
                # Select birth year
                min_year = datetime.now().year - 65
                max_year = datetime.now().year - 18
                birth_year = str(random.randint(min_year, max_year))
                self.page.select_option('select[title="Year:"]', value=birth_year)
                time.sleep(random.uniform(0.5, 1))
                
                # Continue
                self.page.click('button:has-text("Next")')
                time.sleep(random.uniform(2, 3))
            
            # Handle verification
            if self.page.is_visible('text=Verify your email') or self.page.is_visible('text=Verify your phone'):
                verification_result = self.handle_verification('instagram')
                if verification_result['status'] != 'success':
                    return verification_result
            
            # Upload profile picture if available
            if profile_picture_path and os.path.exists(profile_picture_path) and self.page.is_visible('text="Add a Profile Picture"'):
                print(f"Uploading profile picture from: {profile_picture_path}")
                try:
                    # Instagram uses a file input for profile pictures
                    file_input = self.page.locator('input[type="file"]')
                    if file_input:
                        file_input.set_input_files(profile_picture_path)
                        time.sleep(random.uniform(3, 5)) # Wait for upload
                        # Click 'Done' or 'Next' if available after upload
                        if self.page.is_visible('button:has-text("Done")'):
                            self.page.click('button:has-text("Done")')
                        elif self.page.is_visible('button:has-text("Next")'):
                            self.page.click('button:has-text("Next")')
                        print("Profile picture uploaded.")
                    else:
                        print("File input for profile picture not found, skipping upload.")
                        if self.page.is_visible('text=Skip'):
                            self.page.click('text=Skip') # Skip if input not found
                except Exception as upload_e:
                    print(f"Error uploading profile picture: {upload_e}")
                    self.notifier.log_failure("Instagram Profile Picture", str(upload_e))
                    if self.page.is_visible('text=Skip'): # Fallback to skip if upload fails
                        self.page.click('text=Skip')
            elif self.page.is_visible('text=Add a Profile Picture'):
                self.page.click('text=Skip') # Skip if no path or not visible
                time.sleep(1)
            
            # Skip notifications
            if self.page.is_visible('button:has-text("Not Now")'):
                self.page.click('button:has-text("Not Now")')
                time.sleep(1)
            
            return {
                'platform': 'instagram',
                'username': username,
                'email': self.email,
                'status': 'success'
            }
        except Exception as e:
            return {
                'platform': 'instagram',
                'error': str(e),
                'status': 'failed'
            }
        finally:
            self.close_browser()

    def register_multiple_platforms(self, platforms, identity=None, profile=None):
        """Register accounts on multiple platforms using consistent identity"""
        results = {}
        for platform in platforms:
            if platform == 'twitter':
                results['twitter'] = self.register_twitter(identity, profile)
            elif platform == 'facebook':
                results['facebook'] = self.register_facebook(identity)
            elif platform == 'instagram':
                results['instagram'] = self.register_instagram(identity, profile)
            # Add more platforms as needed
            time.sleep(random.uniform(1, 3))  # Random delay between registrations
            
        return results
