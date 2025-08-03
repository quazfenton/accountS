import asyncio
import random
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from playwright.async_api import async_playwright, BrowserContext, Browser, Page
import logging

class StealthBrowserAutomation:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        self.screen_resolutions = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1280, 'height': 720},
            {'width': 1600, 'height': 900}
        ]
        
        self.timezones = [
            'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
            'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo',
            'Australia/Sydney', 'America/Toronto'
        ]
        
        self.locales = [
            'en-US', 'en-GB', 'en-CA', 'en-AU', 'fr-FR', 'de-DE', 'es-ES', 'it-IT'
        ]
    
    async def create_stealth_context(self, proxy: str = None) -> Tuple[BrowserContext, Browser, Any]:
        """Create a browser context with advanced stealth features"""
        playwright = await async_playwright().start()
        
        # Random browser selection with weighted preference for Chrome
        browser_type = random.choices(['chromium', 'firefox'], weights=[0.8, 0.2])[0]
        
        # Advanced launch options
        launch_options = {
            'headless': True,
            'args': self._get_stealth_args(browser_type),
            'ignore_default_args': ['--enable-automation'],
            'slow_mo': random.uniform(50, 150)  # Add slight delay between actions
        }
        
        if proxy:
            launch_options['proxy'] = {'server': f'http://{proxy}'}
        
        # Launch browser
        if browser_type == 'chromium':
            browser = await playwright.chromium.launch(**launch_options)
        else:
            browser = await playwright.firefox.launch(**launch_options)
        
        # Create context with randomized settings
        resolution = random.choice(self.screen_resolutions)
        context_options = {
            'viewport': resolution,
            'user_agent': random.choice(self.user_agents),
            'locale': random.choice(self.locales),
            'timezone_id': random.choice(self.timezones),
            'permissions': ['geolocation'],
            'geolocation': self._get_random_geolocation(),
            'color_scheme': random.choice(['light', 'dark']),
            'reduced_motion': random.choice(['reduce', 'no-preference']),
            'forced_colors': random.choice(['none', 'active']),
            'extra_http_headers': self._get_realistic_headers()
        }
        
        context = await browser.new_context(**context_options)
        
        # Add comprehensive stealth scripts
        await self._inject_stealth_scripts(context)
        
        return context, browser, playwright
    
    def _get_stealth_args(self, browser_type: str) -> List[str]:
        """Get browser-specific stealth arguments"""
        common_args = [
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-translate',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-client-side-phishing-detection',
            '--disable-sync',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
        
        if browser_type == 'chromium':
            chrome_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Faster loading
                '--disable-javascript-harmony-shipping',
                '--disable-background-networking',
                '--disable-background-sync',
                '--disable-device-discovery-notifications',
                '--disable-software-rasterizer',
                '--disable-features=VizDisplayCompositor'
            ]
            return common_args + chrome_args
        else:
            firefox_args = [
                '--disable-extensions',
                '--disable-plugins',
                '--disable-web-security'
            ]
            return common_args + firefox_args
    
    def _get_random_geolocation(self) -> Dict[str, float]:
        """Get random but realistic geolocation"""
        locations = [
            {'latitude': 40.7128, 'longitude': -74.0060},  # New York
            {'latitude': 34.0522, 'longitude': -118.2437}, # Los Angeles
            {'latitude': 41.8781, 'longitude': -87.6298},  # Chicago
            {'latitude': 51.5074, 'longitude': -0.1278},   # London
            {'latitude': 48.8566, 'longitude': 2.3522},    # Paris
            {'latitude': 35.6762, 'longitude': 139.6503},  # Tokyo
        ]
        location = random.choice(locations)
        # Add small random offset
        location['latitude'] += random.uniform(-0.1, 0.1)
        location['longitude'] += random.uniform(-0.1, 0.1)
        return location
    
    def _get_realistic_headers(self) -> Dict[str, str]:
        """Get realistic HTTP headers"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    async def _inject_stealth_scripts(self, context: BrowserContext):
        """Inject comprehensive stealth scripts"""
        stealth_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Mock plugins with realistic data
        Object.defineProperty(navigator, 'plugins', {
            get: () => ({
                length: 3,
                0: {name: 'Chrome PDF Plugin', description: 'Portable Document Format'},
                1: {name: 'Chrome PDF Viewer', description: 'PDF Viewer'},
                2: {name: 'Native Client', description: 'Native Client'}
            })
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Add chrome object for Chromium browsers
        if (!window.chrome) {
            window.chrome = {
                runtime: {},
                loadTimes: function() {
                    return {
                        commitLoadTime: Date.now() / 1000 - Math.random() * 100,
                        finishDocumentLoadTime: Date.now() / 1000 - Math.random() * 50,
                        finishLoadTime: Date.now() / 1000 - Math.random() * 10,
                        firstPaintAfterLoadTime: Date.now() / 1000 - Math.random() * 5,
                        firstPaintTime: Date.now() / 1000 - Math.random() * 10,
                        navigationType: 'Other',
                        npnNegotiatedProtocol: 'h2',
                        requestTime: Date.now() / 1000 - Math.random() * 200,
                        startLoadTime: Date.now() / 1000 - Math.random() * 150,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: true,
                        wasNpnNegotiated: true
                    };
                },
                csi: function() {
                    return {
                        onloadT: Date.now(),
                        pageT: Math.random() * 1000,
                        startE: Date.now() - Math.random() * 1000,
                        tran: Math.floor(Math.random() * 20)
                    };
                }
            };
        }
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
        
        // Override getContext to avoid canvas fingerprinting
        const getContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            if (type === '2d') {
                const context = getContext.call(this, type, ...args);
                const originalFillText = context.fillText;
                context.fillText = function(text, x, y, maxWidth) {
                    // Add slight randomization to avoid fingerprinting
                    return originalFillText.call(this, text, x + Math.random() * 0.1, y + Math.random() * 0.1, maxWidth);
                };
                return context;
            }
            return getContext.call(this, type, ...args);
        };
        
        // Mock WebGL fingerprinting
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'Intel Inc.';
            }
            if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.call(this, parameter);
        };
        
        // Mock AudioContext fingerprinting
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
            AudioContext.prototype.createAnalyser = function() {
                const analyser = originalCreateAnalyser.call(this);
                const originalGetFloatFrequencyData = analyser.getFloatFrequencyData;
                analyser.getFloatFrequencyData = function(array) {
                    originalGetFloatFrequencyData.call(this, array);
                    // Add slight noise to avoid fingerprinting
                    for (let i = 0; i < array.length; i++) {
                        array[i] += Math.random() * 0.0001;
                    }
                };
                return analyser;
            };
        }
        
        // Mock screen properties with slight randomization
        Object.defineProperty(screen, 'availHeight', {
            get: () => screen.height - Math.floor(Math.random() * 10)
        });
        
        Object.defineProperty(screen, 'availWidth', {
            get: () => screen.width - Math.floor(Math.random() * 10)
        });
        
        // Mock Date.prototype.getTimezoneOffset with slight randomization
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        Date.prototype.getTimezoneOffset = function() {
            return originalGetTimezoneOffset.call(this) + Math.floor(Math.random() * 2);
        };
        
        // Remove automation indicators
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """
        
        await context.add_init_script(stealth_script)
    
    async def human_like_typing(self, page: Page, selector: str, text: str, clear_first: bool = True):
        """Type text with human-like delays and occasional typos"""
        try:
            # Wait for element and click
            await page.wait_for_selector(selector, timeout=10000)
            await page.click(selector)
            
            if clear_first:
                await page.keyboard.press('Control+a')
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Type with human-like behavior
            for i, char in enumerate(text):
                # Variable typing speed
                if char == ' ':
                    delay = random.uniform(0.1, 0.3)  # Longer pause for spaces
                elif char in '.,!?':
                    delay = random.uniform(0.2, 0.4)  # Pause for punctuation
                else:
                    delay = random.uniform(0.05, 0.15)
                
                # Occasional typo and correction
                if random.random() < 0.02 and i > 2 and char.isalpha():  # 2% chance
                    # Make a typo
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    await page.keyboard.type(wrong_char, delay=delay)
                    await asyncio.sleep(random.uniform(0.2, 0.5))  # Pause to "notice" typo
                    await page.keyboard.press('Backspace')
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                
                # Type the correct character
                await page.keyboard.type(char, delay=delay)
                
                # Occasional thinking pause
                if random.random() < 0.05:  # 5% chance
                    await asyncio.sleep(random.uniform(0.5, 2.0))
                
        except Exception as e:
            self.logger.error(f"Error in human_like_typing: {e}")
            # Fallback to simple typing
            await page.fill(selector, text)
    
    async def human_like_mouse_movement(self, page: Page, selector: str):
        """Move mouse to element with human-like curved path"""
        try:
            element = page.locator(selector).first
            box = await element.bounding_box()
            
            if not box:
                return
            
            # Get viewport size
            viewport = page.viewport_size
            start_x = random.randint(100, viewport['width'] - 100)
            start_y = random.randint(100, viewport['height'] - 100)
            
            target_x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
            target_y = box['y'] + box['height'] / 2 + random.uniform(-5, 5)
            
            # Create curved path with multiple control points
            steps = random.randint(20, 35)
            control_x = (start_x + target_x) / 2 + random.uniform(-50, 50)
            control_y = (start_y + target_y) / 2 + random.uniform(-50, 50)
            
            for i in range(steps + 1):
                t = i / steps
                
                # Quadratic Bezier curve
                x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * control_x + t ** 2 * target_x
                y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * control_y + t ** 2 * target_y
                
                # Add small random jitter
                x += random.uniform(-2, 2)
                y += random.uniform(-2, 2)
                
                await page.mouse.move(x, y)
                
                # Variable speed - slower at start and end
                if t < 0.3 or t > 0.7:
                    await asyncio.sleep(random.uniform(0.02, 0.05))
                else:
                    await asyncio.sleep(random.uniform(0.01, 0.03))
            
            # Small pause before clicking
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            self.logger.error(f"Error in human_like_mouse_movement: {e}")
    
    async def human_like_scroll(self, page: Page, direction: str = 'down', amount: int = None):
        """Scroll page with human-like behavior"""
        if amount is None:
            amount = random.randint(200, 800)
        
        # Scroll in small increments
        increments = random.randint(3, 8)
        scroll_per_increment = amount // increments
        
        for i in range(increments):
            if direction == 'down':
                await page.mouse.wheel(0, scroll_per_increment)
            else:
                await page.mouse.wheel(0, -scroll_per_increment)
            
            # Variable pause between scrolls
            await asyncio.sleep(random.uniform(0.1, 0.4))
    
    async def random_mouse_movements(self, page: Page, count: int = None):
        """Make random mouse movements to appear more human"""
        if count is None:
            count = random.randint(2, 5)
        
        viewport = page.viewport_size
        
        for _ in range(count):
            x = random.randint(50, viewport['width'] - 50)
            y = random.randint(50, viewport['height'] - 50)
            
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.5, 2.0))
    
    async def simulate_reading_behavior(self, page: Page):
        """Simulate human reading behavior with pauses and scrolling"""
        # Random reading time
        reading_time = random.uniform(3, 8)
        
        # Scroll down slowly while "reading"
        scroll_count = random.randint(2, 4)
        scroll_interval = reading_time / scroll_count
        
        for _ in range(scroll_count):
            await asyncio.sleep(scroll_interval)
            await self.human_like_scroll(page, 'down', random.randint(100, 300))
        
        # Final pause
        await asyncio.sleep(random.uniform(1, 3))
    
    async def wait_with_random_activity(self, page: Page, base_wait: float):
        """Wait while performing random activities to appear human"""
        total_wait = base_wait + random.uniform(-base_wait * 0.3, base_wait * 0.3)
        
        activities = [
            lambda: self.random_mouse_movements(page, 1),
            lambda: self.human_like_scroll(page, random.choice(['up', 'down']), random.randint(50, 200)),
            lambda: asyncio.sleep(random.uniform(0.5, 2.0))
        ]
        
        elapsed = 0
        while elapsed < total_wait:
            activity_time = random.uniform(0.5, 2.0)
            
            # Perform random activity
            activity = random.choice(activities)
            await activity()
            
            elapsed += activity_time
            
            if elapsed < total_wait:
                await asyncio.sleep(min(activity_time, total_wait - elapsed))
                elapsed += activity_time