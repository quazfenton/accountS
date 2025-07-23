import requests
import json
from config.config import Config

class Browserless:
    def __init__(self):
        self.config = Config()
        self.base_url = self.config.BROWSERLESS_URL
        self.api_key = self.config.BROWSERLESS_API_KEY
        
    def execute_script(self, script, context=None):
        """Execute a Playwright script via Browserless API"""
        payload = {
            "code": script,
            "context": context or {},
            "browserWSEndpoint": f"wss://chrome.browserless.io?token={self.api_key}"
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{self.base_url}/playwright",
            data=json.dumps(payload),
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Browserless error: {response.text}")