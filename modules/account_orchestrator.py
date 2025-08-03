import asyncio
import random
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from modules.improved_email_registration import ImprovedEmailRegistration
from modules.social_media_registration import SocialMediaRegistration
from modules.advanced_verification_solver import AdvancedVerificationSolver, VerificationContext, VerificationType
from modules.profile_manager import ProfileManager
from utils.identity_generator import IdentityGenerator
from utils.proxy_manager import ImprovedProxyManager
from utils.monitoring import MetricsCollector, AccountCreationMetric
from utils.stealth_browser import StealthBrowserAutomation

class AccountStatus(Enum):
    CREATED = "created"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    FAILED = "failed"
    REQUIRES_INTERVENTION = "requires_intervention"

@dataclass
class AccountInfo:
    platform: str
    email: str
    username: str
    password: str
    status: AccountStatus
    created_at: datetime
    verification_method: Optional[str] = None
    phone_number: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    requires_human_intervention: bool = False

@dataclass
class AccountEcosystem:
    primary_account: AccountInfo
    linked_accounts: List[AccountInfo]
    identity_seed: str
    creation_strategy: str
    total_creation_time: float
    success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary_account': asdict(self.primary_account),
            'linked_accounts': [asdict(acc) for acc in self.linked_accounts],
            'identity_seed': self.identity_seed,
            'creation_strategy': self.creation_strategy,
            'total_creation_time': self.total_creation_time,
            'success_rate': self.success_rate,
            'created_at': datetime.now().isoformat()
        }

class AccountOrchestrator:
    def __init__(self, proxy_manager: ImprovedProxyManager = None, metrics_collector: MetricsCollector = None):
        self.logger = logging.getLogger(__name__)
        self.proxy_manager = proxy_manager
        self.metrics_collector = metrics_collector
        
        # Initialize components
        self.profile_manager = ProfileManager()
        self.identity_generator = IdentityGenerator()
        self.verification_solver = AdvancedVerificationSolver()
        self.browser_automation = StealthBrowserAutomation()
        
        # Platform-specific handlers
        self.platform_handlers = {
            'email': ImprovedEmailRegistration(proxy_manager, metrics_collector),
            'twitter': None,  # Will be initialized when needed
            'facebook': None,
            'instagram': None,
            'linkedin': None,
            'tiktok': None
        }
        
        # Account creation strategies
        self.creation_strategies = {
            'sequential': self._create_accounts_sequential,
            'parallel': self._create_accounts_parallel,
            'staged': self._create_accounts_staged,
            'ecosystem': self._create_account_ecosystem_advanced
        }
        
        # Platform dependencies and linking strategies
        self.platform_dependencies = {
            'twitter': {'requires': ['email'], 'optional': ['phone']},
            'facebook': {'requires': ['email'], 'optional': ['phone']},
            'instagram': {'requires': ['email'], 'optional': ['phone', 'facebook']},
            'linkedin': {'requires': ['email'], 'optional': ['phone']},
            'tiktok': {'requires': ['email'], 'optional': ['phone']}
        }
        
        # Success rate tracking
        self.platform_success_rates = {}
        self.recent_failures = {}
    
    async def create_account_ecosystem(self, identity_seed: str, platforms: List[str], strategy: str = 'ecosystem') -> AccountEcosystem:
        """Create a complete account ecosystem across multiple platforms"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Creating account ecosystem for platforms: {platforms} using strategy: {strategy}")
            
            # Generate base identity
            self.identity_generator.set_seed(hash(identity_seed))
            base_profile = self.profile_manager.generate_full_profile(seed=hash(identity_seed))
            
            # Select and execute creation strategy
            strategy_func = self.creation_strategies.get(strategy, self._create_account_ecosystem_advanced)
            primary_account, linked_accounts = await strategy_func(base_profile, platforms)
            
            # Calculate metrics
            total_time = time.time() - start_time
            successful_accounts = [acc for acc in [primary_account] + linked_accounts if acc.status in [AccountStatus.CREATED, AccountStatus.VERIFIED]]
            success_rate = len(successful_accounts) / (len(linked_accounts) + 1)
            
            ecosystem = AccountEcosystem(
                primary_account=primary_account,
                linked_accounts=linked_accounts,
                identity_seed=identity_seed,
                creation_strategy=strategy,
                total_creation_time=total_time,
                success_rate=success_rate
            )
            
            self.logger.info(f"Account ecosystem created: {len(successful_accounts)}/{len(platforms)+1} accounts successful")
            return ecosystem
            
        except Exception as e:
            self.logger.error(f"Failed to create account ecosystem: {e}")
            # Return partial ecosystem with error information
            return AccountEcosystem(
                primary_account=AccountInfo(
                    platform='email',
                    email='',
                    username='',
                    password='',
                    status=AccountStatus.FAILED,
                    created_at=datetime.now(),
                    error_message=str(e)
                ),
                linked_accounts=[],
                identity_seed=identity_seed,
                creation_strategy=strategy,
                total_creation_time=time.time() - start_time,
                success_rate=0.0
            )
    
    async def _create_account_ecosystem_advanced(self, base_profile: Dict[str, Any], platforms: List[str]) -> Tuple[AccountInfo, List[AccountInfo]]:
        """Advanced ecosystem creation with intelligent platform ordering and linking"""
        
        # Step 1: Create primary email account
        primary_account = await self._create_primary_email_account(base_profile)
        
        if primary_account.status == AccountStatus.FAILED:
            return primary_account, []
        
        # Step 2: Determine optimal platform creation order
        ordered_platforms = self._optimize_platform_order(platforms)
        
        # Step 3: Create linked accounts with intelligent delays and linking
        linked_accounts = []
        
        for platform in ordered_platforms:
            try:
                # Wait between account creations (realistic human behavior)
                delay = self._calculate_inter_platform_delay(platform, len(linked_accounts))
                if delay > 0:
                    self.logger.info(f"Waiting {delay:.1f}s before creating {platform} account")
                    await asyncio.sleep(delay)
                
                # Create platform account
                account = await self._create_platform_account(
                    platform, 
                    base_profile, 
                    primary_account,
                    linked_accounts
                )
                
                linked_accounts.append(account)
                
                # Update success rate tracking
                self._update_platform_success_rate(platform, account.status == AccountStatus.CREATED)
                
                # Handle account linking if successful
                if account.status in [AccountStatus.CREATED, AccountStatus.VERIFIED]:
                    await self._handle_account_linking(account, primary_account, linked_accounts)
                
            except Exception as e:
                self.logger.error(f"Error creating {platform} account: {e}")
                failed_account = AccountInfo(
                    platform=platform,
                    email=primary_account.email,
                    username='',
                    password='',
                    status=AccountStatus.FAILED,
                    created_at=datetime.now(),
                    error_message=str(e)
                )
                linked_accounts.append(failed_account)
        
        return primary_account, linked_accounts
    
    async def _create_primary_email_account(self, base_profile: Dict[str, Any]) -> AccountInfo:
        """Create the primary email account that will be used for other platforms"""
        try:
            email_handler = self.platform_handlers['email']
            identity = base_profile['basic']
            
            # Try multiple email providers if needed
            providers = ['gmail', 'yahoo', 'outlook']
            
            for provider in providers:
                try:
                    result = await email_handler.register_email(identity, provider=provider)
                    
                    if result['success']:
                        return AccountInfo(
                            platform='email',
                            email=result['email'],
                            username=identity['username'],
                            password=result['password'],
                            status=AccountStatus.CREATED if result.get('status') == 'created' else AccountStatus.PENDING_VERIFICATION,
                            created_at=datetime.now(),
                            verification_method=result.get('verification_method'),
                            profile_data=base_profile
                        )
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create {provider} account: {e}")
                    continue
            
            # All providers failed
            return AccountInfo(
                platform='email',
                email='',
                username='',
                password='',
                status=AccountStatus.FAILED,
                created_at=datetime.now(),
                error_message='All email providers failed'
            )
            
        except Exception as e:
            return AccountInfo(
                platform='email',
                email='',
                username='',
                password='',
                status=AccountStatus.FAILED,
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    async def _create_platform_account(self, platform: str, base_profile: Dict[str, Any], 
                                     primary_account: AccountInfo, existing_accounts: List[AccountInfo]) -> AccountInfo:
        """Create account for specific social media platform"""
        try:
            # Initialize platform handler if not already done
            if not self.platform_handlers.get(platform):
                self.platform_handlers[platform] = SocialMediaRegistration(
                    email=primary_account.email,
                    password=primary_account.password,
                    proxy=None  # Will be handled by proxy manager
                )
            
            handler = self.platform_handlers[platform]
            
            # Prepare platform-specific profile data
            platform_profile = self._adapt_profile_for_platform(base_profile, platform)
            
            # Create account with enhanced error handling
            result = await self._create_platform_account_with_verification(
                handler, platform, platform_profile, primary_account
            )
            
            return AccountInfo(
                platform=platform,
                email=primary_account.email,
                username=result.get('username', ''),
                password=primary_account.password,
                status=self._determine_account_status(result),
                created_at=datetime.now(),
                verification_method=result.get('verification_method'),
                phone_number=result.get('phone_number'),
                profile_data=platform_profile,
                error_message=result.get('error'),
                requires_human_intervention=result.get('requires_human_intervention', False)
            )
            
        except Exception as e:
            return AccountInfo(
                platform=platform,
                email=primary_account.email,
                username='',
                password='',
                status=AccountStatus.FAILED,
                created_at=datetime.now(),
                error_message=str(e)
            )
    
    async def _create_platform_account_with_verification(self, handler, platform: str, 
                                                       profile: Dict[str, Any], primary_account: AccountInfo) -> Dict[str, Any]:
        """Create platform account with comprehensive verification handling"""
        try:
            # Use stealth browser for account creation
            context, browser, playwright = await self.browser_automation.create_stealth_context()
            page = await context.new_page()
            
            try:
                # Navigate to platform signup page
                signup_urls = {
                    'twitter': 'https://twitter.com/i/flow/signup',
                    'facebook': 'https://www.facebook.com/reg/',
                    'instagram': 'https://www.instagram.com/accounts/emailsignup/',
                    'linkedin': 'https://www.linkedin.com/signup',
                    'tiktok': 'https://www.tiktok.com/signup'
                }
                
                signup_url = signup_urls.get(platform)
                if not signup_url:
                    return {'success': False, 'error': f'Unsupported platform: {platform}'}
                
                await page.goto(signup_url, wait_until='networkidle')
                
                # Fill registration form
                await self._fill_platform_registration_form(page, platform, profile, primary_account)
                
                # Handle any verification challenges
                verification_result = await self._handle_platform_verification_challenges(page, platform)
                
                if verification_result.get('requires_human_intervention'):
                    return {
                        'success': False,
                        'error': 'Human intervention required',
                        'requires_human_intervention': True
                    }
                
                # Check registration success
                success = await self._check_platform_registration_success(page, platform)
                
                if success:
                    return {
                        'success': True,
                        'username': profile['basic']['username'],
                        'verification_method': verification_result.get('method'),
                        'phone_number': verification_result.get('phone_number')
                    }
                else:
                    return {'success': False, 'error': 'Registration verification failed'}
                
            finally:
                await context.close()
                await browser.close()
                await playwright.stop()
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _handle_platform_verification_challenges(self, page, platform: str) -> Dict[str, Any]:
        """Handle various verification challenges that may appear during registration"""
        try:
            # Check for different types of verification
            verification_types = [
                (VerificationType.CAPTCHA_IMAGE, 'img[src*="captcha"]'),
                (VerificationType.RECAPTCHA, 'iframe[src*="recaptcha"]'),
                (VerificationType.HCAPTCHA, 'iframe[src*="hcaptcha"]'),
                (VerificationType.SMS, 'input[type="tel"], input[placeholder*="phone"]'),
                (VerificationType.EMAIL, 'text=verify your email, text=check your email')
            ]
            
            for verification_type, selector in verification_types:
                if await page.is_visible(selector):
                    self.logger.info(f"Detected {verification_type.value} verification for {platform}")
                    
                    # Create verification context
                    context = VerificationContext(
                        verification_type=verification_type,
                        platform=platform,
                        page_url=page.url,
                        element_selectors=self._get_platform_verification_selectors(platform, verification_type),
                        metadata={'platform': platform}
                    )
                    
                    # Solve verification
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
    
    def _optimize_platform_order(self, platforms: List[str]) -> List[str]:
        """Optimize the order of platform creation based on dependencies and success rates"""
        # Sort by success rate (highest first) and dependencies
        def platform_score(platform):
            success_rate = self.platform_success_rates.get(platform, 0.5)
            dependency_count = len(self.platform_dependencies.get(platform, {}).get('requires', []))
            recent_failures = self.recent_failures.get(platform, 0)
            
            # Higher score = create earlier
            return success_rate - (dependency_count * 0.1) - (recent_failures * 0.2)
        
        return sorted(platforms, key=platform_score, reverse=True)
    
    def _calculate_inter_platform_delay(self, platform: str, account_count: int) -> float:
        """Calculate realistic delay between platform account creations"""
        base_delays = {
            'twitter': random.uniform(300, 900),    # 5-15 minutes
            'facebook': random.uniform(600, 1800),  # 10-30 minutes
            'instagram': random.uniform(300, 1200), # 5-20 minutes
            'linkedin': random.uniform(900, 2700),  # 15-45 minutes
            'tiktok': random.uniform(300, 900)      # 5-15 minutes
        }
        
        base_delay = base_delays.get(platform, 600)
        
        # Add randomization and account for multiple accounts
        multiplier = 1 + (account_count * 0.2)  # Increase delay for each additional account
        return base_delay * multiplier * random.uniform(0.8, 1.2)
    
    def _adapt_profile_for_platform(self, base_profile: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Adapt profile data for specific platform requirements"""
        adapted_profile = base_profile.copy()
        
        platform_adaptations = {
            'twitter': {
                'bio_length': 160,
                'username_style': 'short',
                'interests': ['tech', 'news', 'entertainment']
            },
            'facebook': {
                'bio_length': 101,
                'username_style': 'real_name',
                'interests': ['friends', 'family', 'local_events']
            },
            'instagram': {
                'bio_length': 150,
                'username_style': 'creative',
                'interests': ['photography', 'lifestyle', 'travel']
            },
            'linkedin': {
                'bio_length': 220,
                'username_style': 'professional',
                'interests': ['career', 'networking', 'industry_news']
            },
            'tiktok': {
                'bio_length': 80,
                'username_style': 'fun',
                'interests': ['entertainment', 'music', 'trends']
            }
        }
        
        if platform in platform_adaptations:
            adaptations = platform_adaptations[platform]
            
            # Adapt bio length
            if 'bio' in adapted_profile.get('personal', {}):
                bio = adapted_profile['personal']['bio']
                max_length = adaptations['bio_length']
                if len(bio) > max_length:
                    adapted_profile['personal']['bio'] = bio[:max_length-3] + '...'
            
            # Adapt username style
            username_style = adaptations['username_style']
            if username_style == 'real_name':
                adapted_profile['basic']['username'] = f"{adapted_profile['basic']['first_name'].lower()}.{adapted_profile['basic']['last_name'].lower()}"
            elif username_style == 'professional':
                adapted_profile['basic']['username'] = f"{adapted_profile['basic']['first_name'].lower()}{adapted_profile['basic']['last_name'].lower()}"
        
        return adapted_profile
    
    async def _fill_platform_registration_form(self, page, platform: str, profile: Dict[str, Any], primary_account: AccountInfo):
        """Fill platform-specific registration form"""
        # This would contain platform-specific form filling logic
        # For now, using generic approach
        
        basic_info = profile['basic']
        
        # Common form fields
        form_mappings = {
            'email': ['input[name="email"]', 'input[type="email"]'],
            'username': ['input[name="username"]', 'input[name="user"]'],
            'password': ['input[name="password"]', 'input[type="password"]'],
            'first_name': ['input[name="first_name"]', 'input[name="firstName"]'],
            'last_name': ['input[name="last_name"]', 'input[name="lastName"]']
        }
        
        for field, selectors in form_mappings.items():
            value = basic_info.get(field, primary_account.email if field == 'email' else '')
            
            for selector in selectors:
                if await page.is_visible(selector):
                    await self.browser_automation.human_like_typing(page, selector, value)
                    break
    
    async def _check_platform_registration_success(self, page, platform: str) -> bool:
        """Check if platform registration was successful"""
        success_indicators = {
            'twitter': ['text=Welcome to Twitter', 'text=What are you interested in?'],
            'facebook': ['text=Welcome to Facebook', 'text=Find friends'],
            'instagram': ['text=Welcome to Instagram', 'text=Find people to follow'],
            'linkedin': ['text=Welcome to LinkedIn', 'text=Build your network'],
            'tiktok': ['text=Welcome to TikTok', 'text=For You']
        }
        
        indicators = success_indicators.get(platform, ['text=Welcome', 'text=Success'])
        
        for indicator in indicators:
            if await page.is_visible(indicator):
                return True
        
        return False
    
    def _get_platform_verification_selectors(self, platform: str, verification_type: VerificationType) -> Dict[str, str]:
        """Get platform-specific selectors for verification elements"""
        # This would return platform-specific selectors
        # For now, returning generic selectors
        return {
            'phone_input': 'input[type="tel"]',
            'code_input': 'input[name="code"]',
            'send_button': 'button:has-text("Send")',
            'submit_button': 'button[type="submit"]',
            'captcha_image': 'img[src*="captcha"]',
            'captcha_input': 'input[name="captcha"]'
        }
    
    def _determine_account_status(self, result: Dict[str, Any]) -> AccountStatus:
        """Determine account status from creation result"""
        if result.get('success'):
            if result.get('requires_verification'):
                return AccountStatus.PENDING_VERIFICATION
            else:
                return AccountStatus.CREATED
        elif result.get('requires_human_intervention'):
            return AccountStatus.REQUIRES_INTERVENTION
        else:
            return AccountStatus.FAILED
    
    async def _handle_account_linking(self, new_account: AccountInfo, primary_account: AccountInfo, existing_accounts: List[AccountInfo]):
        """Handle linking between accounts (following, friending, etc.)"""
        # This would implement cross-platform account linking
        # For now, just logging the opportunity
        self.logger.info(f"Account linking opportunity: {new_account.platform} -> {primary_account.platform}")
    
    def _update_platform_success_rate(self, platform: str, success: bool):
        """Update success rate tracking for platform"""
        if platform not in self.platform_success_rates:
            self.platform_success_rates[platform] = 0.5
        
        # Simple exponential moving average
        current_rate = self.platform_success_rates[platform]
        new_rate = current_rate * 0.8 + (1.0 if success else 0.0) * 0.2
        self.platform_success_rates[platform] = new_rate
        
        # Track recent failures
        if not success:
            self.recent_failures[platform] = self.recent_failures.get(platform, 0) + 1
        else:
            self.recent_failures[platform] = 0
    
    # Additional strategy implementations
    async def _create_accounts_sequential(self, base_profile: Dict[str, Any], platforms: List[str]) -> Tuple[AccountInfo, List[AccountInfo]]:
        """Create accounts one by one with delays"""
        return await self._create_account_ecosystem_advanced(base_profile, platforms)
    
    async def _create_accounts_parallel(self, base_profile: Dict[str, Any], platforms: List[str]) -> Tuple[AccountInfo, List[AccountInfo]]:
        """Create accounts in parallel (higher risk but faster)"""
        # Implementation for parallel creation
        return await self._create_account_ecosystem_advanced(base_profile, platforms)
    
    async def _create_accounts_staged(self, base_profile: Dict[str, Any], platforms: List[str]) -> Tuple[AccountInfo, List[AccountInfo]]:
        """Create accounts in stages with longer delays"""
        # Implementation for staged creation
        return await self._create_account_ecosystem_advanced(base_profile, platforms)