import random
import string
import time
import re
import tempfile
import requests
from playwright.sync_api import sync_playwright
from config.config import Config
from utils.identity_generator import IdentityGenerator
from utils.notifier import Notifier
from .detection_prevention import DetectionPrevention
from faker import Faker

class EmailRegistration:
    def __init__(self, headless=True, debug=False):
        self.config = Config()
        self.current_proxy = None
        self.proxy_index = 0
        self.identity_gen = IdentityGenerator()
        self.notifier = Notifier()
        self.headless = headless
        self.debug = debug
        self.fake = Faker()
        self.behavior_profile = self._generate_behavior_profile()
    
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
    
    def rotate_proxy(self):
        """Rotate to the next proxy in the list"""
        if not self.config.PROXY_LIST:
            return None
            
        self.current_proxy = self.config.PROXY_LIST[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.config.PROXY_LIST)
        return self.current_proxy
    
    def _human_type(self, page, selector, text):
        """Simulate human typing with errors and corrections"""
        page.click(selector)
        for i, char in enumerate(text):
            # Random pause between keystrokes
            if random.random() < 0.3:
                time.sleep(random.uniform(0.1, 0.5))
            
            # Simulate typo with correction
            if random.random() < self.behavior_profile['error_rate'] and i > 3:
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz1234567890')
                page.keyboard.press(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                page.keyboard.press('Backspace')
            
            page.keyboard.press(char)
            time.sleep(self.behavior_profile['typing_speed'])
    
    def init_browser(self):
        """Initialize Playwright browser with advanced fingerprint spoofing"""
        with sync_playwright() as p:
            proxy_settings = {
                'server': f'http://{self.current_proxy}'
            } if self.current_proxy else None
            
            self.browser = p.chromium.launch(
                headless=self.headless,
                proxy=proxy_settings,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
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
    
    def register_email(self, retries=3):
        """Register email using web crawling with headless browser"""
        for attempt in range(retries):
            try:
                print(f"[Email Registration] Attempt {attempt+1}/{retries}")
                
                # Rotate proxy
                proxy = self.rotate_proxy()
                print(f"[Proxy] Using proxy: {proxy or 'None'}")
                
                # Initialize browser
                self.init_browser()
                print("[Browser] Initialized")
                
                # Navigate to email provider
                self.page.goto(self.config.EMAIL_SIGNUP_URL)
                print(f"[Navigation] Loaded {self.config.EMAIL_SIGNUP_URL}")
                time.sleep(2)
                
                # Generate identity
                identity = self.identity_gen.generate_identity()
                username = identity['username']
                email = f"{username}@{self.config.EMAIL_DOMAIN}"
                password = identity['password']
                print(f"[Identity] Generated: {email}")
                
                # Fill registration form
                print("[Form] Filling registration form")
                self._human_type(self.page, 'input[name="username"]', username)
                self._human_type(self.page, 'input[name="password"]', password)
                self._human_type(self.page, 'input[name="password_confirm"]', password)
                
                # Solve captchas
                if self.page.is_visible('iframe[title*="recaptcha"]') or self.page.is_visible('img.captcha-image'):
                    print("[Captcha] Detected captcha - solving")
                    if not self.solve_captcha():
                        print("[Captcha] Failed to solve")
                        continue
                
                # Submit form
                self.page.click('button[type="submit"]')
                print("[Form] Submitted")
                time.sleep(3)
                
                # Handle email verification
                if self.page.is_visible('text="Verify your email"'):
                    print("[Verification] Email verification required")
                    # Implementation would depend on specific provider
                    # For now, assume we can skip in demo
                    if self.debug:
                        self.page.pause()
                    return {
                        "email": email,
                        "password": password,
                        "proxy": proxy,
                        "status": "needs_verification"
                    }
                
                print("[Success] Email registration complete")
                return {
                    "email": email,
                    "password": password,
                    "proxy": proxy
                }
                
            except Exception as e:
                print(f"[Error] Registration attempt failed: {str(e)}")
                self.notifier.send_alert(f"Email registration error: {str(e)}")
                
                if self.debug:
                    self.page.pause()
                    
            finally:
                if not self.debug:
                    self.browser.close()
        
        print("[Failure] All registration attempts failed")
        self.notifier.human_intervention_required("Email Registration",
            f"Failed after {retries} attempts")
        return None

    def solve_captcha(self):
        """Solve captcha using external service with screenshot"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                # Get captcha image
                captcha_img = self.page.query_selector('img.captcha-image, .g-recaptcha')
                if captcha_img:
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
                            input_selector = 'input.captcha-input, #g-recaptcha-response'
                            self.page.fill(input_selector, solution)
                            return True
        except Exception as e:
            print(f"Captcha solving failed: {str(e)}")
        
        return False