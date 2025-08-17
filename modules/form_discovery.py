class IntelligentFormDiscovery:
    """Advanced form discovery using multiple strategies"""
    
    def __init__(self, browser_automation):
        self.browser_automation = browser_automation
        self.logger = logging.getLogger(__name__)
        
    async def discover_registration_form(self, page, platform_hints: Dict[str, Any]) -> Dict[str, str]:
        """Discover registration form using multiple strategies"""
        discovered_selectors = {}
        
        # Strategy 1: Use AI-powered element detection
        ai_selectors = await self._ai_powered_element_detection(page, platform_hints)
        discovered_selectors.update(ai_selectors)
        
        # Strategy 2: Pattern-based discovery
        pattern_selectors = await self._pattern_based_discovery(page)
        discovered_selectors.update(pattern_selectors)
        
        # Strategy 3: DOM analysis
        dom_selectors = await self._dom_analysis_discovery(page)
        discovered_selectors.update(dom_selectors)
        
        # Strategy 4: Visual element detection
        visual_selectors = await self._visual_element_detection(page)
        discovered_selectors.update(visual_selectors)
        
        return discovered_selectors
    
    async def _ai_powered_element_detection(self, page, platform_hints: Dict[str, Any]) -> Dict[str, str]:
        """Use AI/ML to identify form elements"""
        try:
            # Take screenshot for visual analysis
            screenshot = await page.screenshot()
            
            # Use computer vision to identify form elements
            # This could integrate with services like:
            # - Google Vision API
            # - AWS Rekognition
            # - Custom trained models
            
            # For now, implement basic OCR-based detection
            import pytesseract
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(screenshot))
            text_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Analyze text to find form-related elements
            form_keywords = {
                'email': ['email', 'e-mail', 'mail address'],
                'password': ['password', 'pass', 'pwd'],
                'username': ['username', 'user name', 'handle'],
                'first_name': ['first name', 'given name', 'fname'],
                'last_name': ['last name', 'surname', 'lname'],
                'submit': ['sign up', 'register', 'create account', 'join']
            }
            
            discovered = {}
            for i, text in enumerate(text_data['text']):
                if text.strip():
                    for field_type, keywords in form_keywords.items():
                        if any(keyword.lower() in text.lower() for keyword in keywords):
                            # Find nearby input elements
                            x, y = text_data['left'][i], text_data['top'][i]
                            selector = await self._find_input_near_coordinates(page, x, y)
                            if selector:
                                discovered[field_type] = selector
                                break
            
            return discovered
            
        except Exception as e:
            self.logger.warning(f"AI-powered detection failed: {e}")
            return {}
    
    async def _pattern_based_discovery(self, page) -> Dict[str, str]:
        """Discover elements using common patterns"""
        patterns = {
            'email': [
                'input[type="email"]',
                'input[name*="email" i]',
                'input[placeholder*="email" i]',
                'input[id*="email" i]',
                'input[autocomplete="email"]'
            ],
            'password': [
                'input[type="password"]',
                'input[name*="password" i]',
                'input[placeholder*="password" i]',
                'input[id*="password" i]',
                'input[autocomplete="new-password"]'
            ],
            'username': [
                'input[name*="username" i]',
                'input[name*="user" i]',
                'input[placeholder*="username" i]',
                'input[id*="username" i]',
                'input[autocomplete="username"]'
            ],
            'first_name': [
                'input[name*="first" i]',
                'input[name*="fname" i]',
                'input[placeholder*="first" i]',
                'input[autocomplete="given-name"]'
            ],
            'last_name': [
                'input[name*="last" i]',
                'input[name*="lname" i]',
                'input[placeholder*="last" i]',
                'input[autocomplete="family-name"]'
            ],
            'submit': [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign up")',
                'button:has-text("Register")',
                'button:has-text("Create")',
                'button:has-text("Join")',
                'button:has-text("Continue")',
                'button:has-text("Next")'
            ]
        }
        
        discovered = {}
        for field_type, selectors in patterns.items():
            for selector in selectors:
                try:
                    if await page.is_visible(selector):
                        discovered[field_type] = selector
                        break
                except:
                    continue
        
        return discovered
    
    async def _dom_analysis_discovery(self, page) -> Dict[str, str]:
        """Analyze DOM structure to find form elements"""
        try:
            # Get all forms on the page
            forms = await page.query_selector_all('form')
            
            discovered = {}
            for form in forms:
                # Analyze form inputs
                inputs = await form.query_selector_all('input, select, textarea')
                
                for input_elem in inputs:
                    # Get element attributes
                    attributes = await page.evaluate('''
                        (element) => {
                            const attrs = {};
                            for (let attr of element.attributes) {
                                attrs[attr.name] = attr.value;
                            }
                            return attrs;
                        }
                    ''', input_elem)
                    
                    # Classify input based on attributes
                    field_type = self._classify_input_element(attributes)
                    if field_type and field_type not in discovered:
                        selector = await self._generate_selector_for_element(page, input_elem)
                        if selector:
                            discovered[field_type] = selector
            
            return discovered
            
        except Exception as e:
            self.logger.warning(f"DOM analysis failed: {e}")
            return {}
    
    def _classify_input_element(self, attributes: Dict[str, str]) -> Optional[str]:
        """Classify input element based on its attributes"""
        # Check type attribute
        input_type = attributes.get('type', '').lower()
        if input_type == 'email':
            return 'email'
        elif input_type == 'password':
            return 'password'
        elif input_type == 'submit':
            return 'submit'
        
        # Check name attribute
        name = attributes.get('name', '').lower()
        if 'email' in name:
            return 'email'
        elif 'password' in name:
            return 'password'
        elif 'username' in name or 'user' in name:
            return 'username'
        elif 'first' in name or 'fname' in name:
            return 'first_name'
        elif 'last' in name or 'lname' in name:
            return 'last_name'
        
        # Check placeholder
        placeholder = attributes.get('placeholder', '').lower()
        if 'email' in placeholder:
            return 'email'
        elif 'password' in placeholder:
            return 'password'
        elif 'username' in placeholder:
            return 'username'
        elif 'first' in placeholder:
            return 'first_name'
        elif 'last' in placeholder:
            return 'last_name'
        
        return None
    
    async def _visual_element_detection(self, page) -> Dict[str, str]:
        """Use visual cues to detect form elements"""
        try:
            # Look for labels and associate them with inputs
            labels = await page.query_selector_all('label')
            discovered = {}
            
            for label in labels:
                label_text = await label.inner_text()
                label_text = label_text.lower().strip()
                
                # Find associated input
                input_selector = None
                
                # Try 'for' attribute
                label_for = await label.get_attribute('for')
                if label_for:
                    input_selector = f'#{label_for}'
                else:
                    # Look for input inside label
                    input_elem = await label.query_selector('input, select, textarea')
                    if input_elem:
                        input_selector = await self._generate_selector_for_element(page, input_elem)
                
                if input_selector:
                    # Classify based on label text
                    if 'email' in label_text:
                        discovered['email'] = input_selector
                    elif 'password' in label_text:
                        discovered['password'] = input_selector
                    elif 'username' in label_text or 'user name' in label_text:
                        discovered['username'] = input_selector
                    elif 'first name' in label_text:
                        discovered['first_name'] = input_selector
                    elif 'last name' in label_text:
                        discovered['last_name'] = input_selector
            
            return discovered
            
        except Exception as e:
            self.logger.warning(f"Visual detection failed: {e}")
