import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Supabase configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Proxy configuration
    PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []
    
    # Email configuration
    EMAIL_DOMAIN = os.getenv('EMAIL_DOMAIN')
    EMAIL_SIGNUP_URL = os.getenv('EMAIL_SIGNUP_URL', 'https://signup.example-email-service.com')
    # Deprecated API-based settings
    EMAIL_API_KEY = os.getenv('EMAIL_API_KEY')
    EMAIL_SERVICE_URL = os.getenv('EMAIL_SERVICE_URL', 'https://api.example-email-service.com/register')
    
    # Social media API keys
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
    FACEBOOK_API_KEY = os.getenv('FACEBOOK_API_KEY')
    INSTAGRAM_API_KEY = os.getenv('INSTAGRAM_API_KEY')
    
    # Captcha handling
    CAPTCHA_API_KEY = os.getenv('CAPTCHA_SOLVER_API_KEY')
    CAPTCHA_SERVICE_URL = os.getenv('CAPTCHA_SERVICE_URL', 'https://api.captchaservice.com/solve')
    
    # SMS verification
    SMS_API_KEY = os.getenv('SMS_VERIFICATION_API_KEY')
    SMS_SERVICE_URL = os.getenv('SMS_SERVICE_URL', 'https://api.sms-service.com')
    
    # SIP configuration
    SIP_SERVER = os.getenv('SIP_SERVER')
    SIP_USERNAME = os.getenv('SIP_USERNAME')
    SIP_PASSWORD = os.getenv('SIP_PASSWORD')
    
    # Browser configuration
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    # Browserless configuration
    BROWSERLESS_API_KEY = os.getenv('BROWSERLESS_API_KEY')
    BROWSERLESS_URL = os.getenv('BROWSERLESS_URL', 'https://chrome.browserless.io')