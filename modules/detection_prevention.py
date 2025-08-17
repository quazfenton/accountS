import random
import json
from playwright.sync_api import BrowserContext

class DetectionPrevention:
    def __init__(self, context: BrowserContext):
        self.context = context
    
    def apply_stealth(self):
        """Apply comprehensive detection prevention techniques with advanced spoofing"""
        # Randomize viewport within common resolutions
        viewports = [
            {"width": 1366, "height": 768},
            {"width": 1920, "height": 1080},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900}
        ]
        viewport = random.choice(viewports)
        self.context.set_viewport_size(viewport)
        
        # Spoof user agent with matching platform
        user_agents = {
            "windows": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
            ],
            "mac": [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
        }
        platform = random.choice(["windows", "mac"])
        user_agent = random.choice(user_agents[platform])
        self.context.set_extra_http_headers({"User-Agent": user_agent})
        
        # Spoof additional navigator properties
        navigator_props = {
            "windows": {
                "platform": "Win32",
                "cpuClass": "x86",
                "oscpu": "Windows NT 10.0; Win64; x64",
                "vendor": "Google Inc.",
                "vendorSub": "",
                "productSub": "20030107"
            },
            "mac": {
                "platform": "MacIntel",
                "cpuClass": None,
                "oscpu": None,
                "vendor": "Apple Computer, Inc.",
                "vendorSub": "",
                "productSub": "20030107"
            }
        }
        nav_props = navigator_props[platform]
        
        # Add navigator property spoofing
        nav_script = f"""
            // Spoof additional navigator properties
            Object.defineProperty(navigator, 'platform', {{get: () => '{nav_props['platform']}'}}});
            """
        
        if nav_props['cpuClass'] is not None:
            nav_script += f"Object.defineProperty(navigator, 'cpuClass', {{get: () => '{nav_props['cpuClass']}'}}});"
        else:
            nav_script += "delete navigator.cpuClass;"
        
        if nav_props['oscpu'] is not None:
            nav_script += f"Object.defineProperty(navigator, 'oscpu', {{get: () => '{nav_props['oscpu']}'}}});"
        else:
            nav_script += "delete navigator.oscpu;"
        
        nav_script += f"""
            Object.defineProperty(navigator, 'vendor', {{get: () => '{nav_props['vendor']}'}}});
            Object.defineProperty(navigator, 'vendorSub', {{get: () => '{nav_props['vendorSub']}'}}});
            Object.defineProperty(navigator, 'productSub', {{get: () => '{nav_props['productSub']}'}}});
            
            // Add webdriver property removal
            delete navigator.webdriver;
            delete navigator.__proto__.webdriver;
        """
        
        self.context.add_init_script(nav_script)
        
        # Spoof webgl fingerprint with vendor-specific values
        webgl_vendors = {
            "Intel Inc.": "Intel Iris OpenGL Engine",
            "Google Inc.": "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
            "NVIDIA Corporation": "NVIDIA GeForce RTX 3080 OpenGL Engine"
        }
        vendor = random.choice(list(webgl_vendors.keys()))
        renderer = webgl_vendors[vendor]
        
        self.context.add_init_script(f"""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{vendor}';
                if (parameter === 37446) return '{renderer}';
                if (parameter === 7937) return 'WebKit WebGL';
                if (parameter === 7938) return 'WebGL 1.0';
                return getParameter(parameter);
            }};
            
            // Spoof WebGL capabilities
            const getExtension = WebGLRenderingContext.prototype.getExtension;
            WebGLRenderingContext.prototype.getExtension = function(extensionName) {{
                if (extensionName === 'WEBGL_debug_renderer_info') {{
                    return {{
                        UNMASKED_VENDOR_WEBGL: '{vendor}',
                        UNMASKED_RENDERER_WEBGL: '{renderer}'
                    }};
                }}
                return getExtension.call(this, extensionName);
            }};
        """)
        
        # Spoof canvas fingerprint with noise injection
        self.context.add_init_script("""
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type, encoderOptions) {
                const image = toDataURL.call(this, type, encoderOptions);
                if (type === 'image/png' || type === 'image/jpeg') {
                    // Add random noise to fingerprint
                    const ctx = this.getContext('2d');
                    const imageData = ctx.getImageData(0, 0, this.width, this.height);
                    const data = imageData.data;
                    
                    // Add 0.1% random noise
                    for (let i = 0; i < data.length; i += 4) {
                        if (Math.random() < 0.001) {
                            data[i] = Math.floor(Math.random() * 255);
                            data[i+1] = Math.floor(Math.random() * 255);
                            data[i+2] = Math.floor(Math.random() * 255);
                        }
                    }
                    ctx.putImageData(imageData, 0, 0);
                }
                return toDataURL.call(this, type, encoderOptions);
            };
        """)
        
        # Spoof audio context with random values
        self.context.add_init_script("""
            const originalCreateOscillator = AudioContext.prototype.createOscillator;
            const originalCreateAnalyser = AudioContext.prototype.createAnalyser;
            
            AudioContext.prototype.createOscillator = function() {
                const oscillator = originalCreateOscillator.apply(this, arguments);
                oscillator.frequency.value = 440 + Math.random() * 20 - 10;
                return oscillator;
            };
            
            AudioContext.prototype.createAnalyser = function() {
                const analyser = originalCreateAnalyser.apply(this, arguments);
                analyser.fftSize = 2048;
                return analyser;
            };
            
            // Spoof AudioBuffer
            const originalCreateBuffer = AudioContext.prototype.createBuffer;
            AudioContext.prototype.createBuffer = function(numOfChannels, length, sampleRate) {
                // Add slight variation to sample rate
                sampleRate = sampleRate + Math.floor(Math.random() * 100) - 50;
                return originalCreateBuffer.call(this, numOfChannels, length, sampleRate);
            };
        """)
        
        # Spoof WebRTC with realistic IP addresses
        self.context.add_init_script("""
            const originalRTCPeerConnection = window.RTCPeerConnection;
            window.RTCPeerConnection = function(config) {
                config = config || {};
                config.iceServers = [{
                    urls: [
                        'stun:stun1.l.google.com:19302',
                        'stun:stun2.l.google.com:19302'
                    ]
                }];
                
                const pc = new originalRTCPeerConnection(config);
                
                // Spoof IP addresses
                const originalGetStats = pc.getStats.bind(pc);
                pc.getStats = async function() {
                    const stats = await originalGetStats();
                    stats.forEach(report => {
                        if (report.type === 'local-candidate' || report.type === 'remote-candidate') {
                            if (report.ip) {
                                report.ip = '192.168.' + Math.floor(Math.random() * 255) + '.' + Math.floor(Math.random() * 255);
                            }
                            if (report.address) {
                                report.address = '192.168.' + Math.floor(Math.random() * 255) + '.' + Math.floor(Math.random() * 255);
                            }
                        }
                    });
                    return stats;
                };
                
                return pc;
            };
        """)

        # Spoof hardware concurrency
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => Math.floor(Math.random() * 4) + 2 }); // 2-5 cores
        """)

        # Spoof battery status API
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'getBattery', {
                value: () => Promise.resolve({
                    charging: Math.random() > 0.5,
                    chargingTime: Infinity,
                    dischargingTime: Math.random() * 10000,
                    level: Math.random() * 0.2 + 0.8 // 80-100%
                })
            });
        """)

        # Spoof font fingerprinting (basic example, more complex methods exist)
        self.context.add_init_script("""
            const originalQuery = document.fonts.query;
            document.fonts.query = function(font) {
                // Always return true for common fonts to avoid detection
                if (font.includes('Arial') || font.includes('Times New Roman')) {
                    return true;
                }
                return originalQuery.call(this, font);
            };
        """)
        
        # Enhanced screen properties spoofing
        screen_script = """
            // Spoof screen dimensions
            Object.defineProperty(window.screen, 'width', { get: () => %d });
            Object.defineProperty(window.screen, 'height', { get: () => %d });
            Object.defineProperty(window.screen, 'availWidth', { get: () => %d });
            Object.defineProperty(window.screen, 'availHeight', { get: () => %d });
            Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
        """ % (viewport["width"], viewport["height"], viewport["width"], viewport["height"] - 100)  # 100px for browser UI
        
        self.context.add_init_script(screen_script)
        
        # Spoof timezone and locale
        timezones = {
            'en-US': ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles'],
            'en-GB': ['Europe/London'],
            'en-CA': ['America/Toronto', 'America/Vancouver']
        }
        
        locale = random.choice(['en-US', 'en-GB', 'en-CA'])
        timezone = random.choice(timezones[locale])
        
        timezone_script = f"""
            // Spoof timezone
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                value: function() {{
                    return {{
                        ...this.__proto__.resolvedOptions.call(this),
                        timeZone: '{timezone}',
                        locale: '{locale}'
                    }};
                }}
            }});
        """
        
        self.context.add_init_script(timezone_script)
        
        # Spoof device memory
        memory_values = [2, 4, 8]  # GB values
        memory = random.choice(memory_values)
        
        memory_script = f"""
            // Spoof device memory
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {memory},
                configurable: false
            }});
        """
        
        self.context.add_init_script(memory_script)
    
    def rotate_fingerprint(self):
        """Rotate browser fingerprint with new properties"""
        # Create new context with fresh fingerprint
        new_context = self.context.browser.new_context(
            viewport=random.choice([
                {"width": 1366, "height": 768},
                {"width": 1920, "height": 1080},
                {"width": 1536, "height": 864},
                {"width": 1440, "height": 900}
            ]),
            user_agent=random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
            ]),
            locale=random.choice(['en-US', 'en-GB', 'en-CA']),
            timezone_id=random.choice(['America/New_York', 'Europe/London', 'Australia/Sydney']),
            geolocation={
                'longitude': -122.4194 + random.uniform(-0.5, 0.5),
                'latitude': 37.7749 + random.uniform(-0.5, 0.5)
            },
            permissions=['geolocation']
        )
        
        # Close old context and replace with new
        self.context.close()
        self.context = new_context
        self.apply_stealth()