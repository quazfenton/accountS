from typing import Dict, Protocol, runtime_checkable, Optional, Any, List
from abc import abstractmethod
import importlib
import os
from pathlib import Path

@runtime_checkable
class PlatformHandler(Protocol):
    """Protocol for platform handlers"""
    
    async def create_account(self, identity: Dict[str, Any], proxy: str = None) -> Dict[str, Any]:
        """Create an account on this platform"""
        ...
    
    async def verify_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify an account on this platform"""
        ...

class PluginManager:
    """Manage platform handler plugins"""
    
    def __init__(self):
        self._handlers: Dict[str, PlatformHandler] = {}
        self._handler_classes: Dict[str, type] = {}
    
    def register_handler(self, platform_name: str, handler: PlatformHandler):
        """Register a platform handler"""
        if not isinstance(handler, PlatformHandler):
            raise TypeError(f"Handler must implement PlatformHandler protocol")
        self._handlers[platform_name] = handler
    
    def register_handler_class(self, platform_name: str, handler_class: type):
        """Register a platform handler class (to be instantiated when needed)"""
        self._handler_classes[platform_name] = handler_class
    
    def get_handler(self, platform_name: str) -> Optional[PlatformHandler]:
        """Get a platform handler, instantiating if needed"""
        # First check if we have an instance
        if platform_name in self._handlers:
            return self._handlers[platform_name]
        
        # If not, check if we have a class we can instantiate
        if platform_name in self._handler_classes:
            handler_class = self._handler_classes[platform_name]
            handler_instance = handler_class()  # Initialize the handler
            self._handlers[platform_name] = handler_instance
            return handler_instance
        
        return None
    
    def list_available_platforms(self) -> List[str]:
        """List all available platforms"""
        return list(set(self._handlers.keys()) | set(self._handler_classes.keys()))
    
    def load_handlers_from_directory(self, directory_path: str):
        """Dynamically load all platform handlers from a directory"""
        directory = Path(directory_path)
        
        # Get all Python files in the directory
        for py_file in directory.glob("*.py"):
            if py_file.name.startswith('__'):
                continue
                
            module_name = py_file.stem
            
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for classes that implement PlatformHandler
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        attr is not PlatformHandler and 
                        PlatformHandler in attr.__bases__ or
                        hasattr(attr, 'create_account') and hasattr(attr, 'verify_account')):
                        
                        # Check if it's a proper platform handler
                        import inspect
                        if (hasattr(attr, 'create_account') and 
                            hasattr(attr, 'verify_account') and
                            inspect.ismethod(getattr(attr, 'create_account')) or 
                            inspect.isfunction(getattr(attr, 'create_account'))):
                            
                            # Register the handler class
                            platform_name = attr_name.lower().replace('handler', '')
                            self.register_handler_class(platform_name, attr)
                            
            except Exception as e:
                print(f"Error loading handler from {py_file}: {e}")

# Global plugin manager instance
plugin_manager = PluginManager()

# Example concrete implementation of a platform handler
class TwitterHandler:
    """Twitter platform handler implementation"""
    
    def __init__(self):
        self.platform_name = 'twitter'
        # Initialize any required services
        from utils.stealth_browser import StealthBrowserAutomation
        self.browser_automation = StealthBrowserAutomation()
    
    async def create_account(self, identity: Dict[str, Any], proxy: str = None) -> Dict[str, Any]:
        """Create an account on Twitter"""
        try:
            # Create browser context with proxy if provided
            context = await self.browser_automation.create_context(proxy=proxy)
            page = await context.new_page()
            
            # Navigate to Twitter signup
            await page.goto("https://twitter.com/i/flow/signup", wait_until="networkidle")
            
            # Implementation would go here
            # This is a simplified version
            await page.wait_for_timeout(5000)  # Wait for page to load
            
            return {
                'success': False,
                'error': 'Twitter handler implementation not complete',
                'platform': 'twitter',
                'email': identity.get('email')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'twitter',
                'email': identity.get('email')
            }
        finally:
            if 'context' in locals():
                await context.close()
    
    async def verify_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a Twitter account"""
        try:
            # Verification implementation
            return {
                'success': True,
                'verified': True,
                'platform': 'twitter',
                'email': account_data.get('email')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'twitter',
                'email': account_data.get('email')
            }

# Register the Twitter handler
plugin_manager.register_handler_class('twitter', TwitterHandler)