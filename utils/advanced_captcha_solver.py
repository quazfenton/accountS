import asyncio
import base64
import time
import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

class CaptchaType(Enum):
    IMAGE = "image"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    FUNCAPTCHA = "funcaptcha"
    GEETEST = "geetest"

@dataclass
class CaptchaTask:
    task_id: str
    service: str
    captcha_type: CaptchaType
    created_at: float
    max_wait_time: int = 300
    
    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.max_wait_time

class AdvancedCaptchaSolver:
    def __init__(self):
        self.services = {
            '2captcha': TwoCaptchaService(),
            'anticaptcha': AntiCaptchaService(),
            'deathbycaptcha': DeathByCaptchaService(),
            'capmonster': CapMonsterService()
        }
        self.service_priority = ['2captcha', 'anticaptcha', 'capmonster', 'deathbycaptcha']
        self.active_tasks: Dict[str, CaptchaTask] = {}
        self.logger = logging.getLogger(__name__)
        
        # Service performance tracking
        self.service_stats = {
            service: {
                'successes': 0,
                'failures': 0,
                'avg_solve_time': 0,
                'last_success': None
            } for service in self.services.keys()
        }
    
    async def solve_captcha(self, captcha_type: CaptchaType, **kwargs) -> Dict[str, Any]:
        """Solve captcha with automatic service fallback"""
        
        # Get best available service
        service_name = self._get_best_service(captcha_type)
        if not service_name:
            return {'success': False, 'error': 'No available captcha services'}
        
        # Try primary service
        result = await self._solve_with_service(service_name, captcha_type, **kwargs)
        
        # If primary service fails, try fallback services
        if not result['success']:
            for fallback_service in self.service_priority:
                if fallback_service != service_name and fallback_service in self.services:
                    self.logger.info(f"Trying fallback service: {fallback_service}")
                    result = await self._solve_with_service(fallback_service, captcha_type, **kwargs)
                    if result['success']:
                        break
        
        return result
    
    async def _solve_with_service(self, service_name: str, captcha_type: CaptchaType, **kwargs) -> Dict[str, Any]:
        """Solve captcha with specific service"""
        service = self.services[service_name]
        start_time = time.time()
        
        try:
            result = await service.solve(captcha_type, **kwargs)
            solve_time = time.time() - start_time
            
            if result['success']:
                self._record_service_success(service_name, solve_time)
                self.logger.info(f"Captcha solved by {service_name} in {solve_time:.2f}s")
            else:
                self._record_service_failure(service_name)
                self.logger.warning(f"Captcha solving failed with {service_name}: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            self._record_service_failure(service_name)
            self.logger.error(f"Exception in {service_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_best_service(self, captcha_type: CaptchaType) -> Optional[str]:
        """Get the best service for the given captcha type"""
        available_services = []
        
        for service_name, service in self.services.items():
            if service.supports_captcha_type(captcha_type) and service.is_available():
                stats = self.service_stats[service_name]
                total_attempts = stats['successes'] + stats['failures']
                success_rate = stats['successes'] / max(total_attempts, 1)
                
                available_services.append({
                    'name': service_name,
                    'success_rate': success_rate,
                    'avg_solve_time': stats['avg_solve_time'],
                    'total_attempts': total_attempts
                })
        
        if not available_services:
            return None
        
        # Sort by success rate, then by solve time
        available_services.sort(key=lambda x: (x['success_rate'], -x['avg_solve_time']), reverse=True)
        return available_services[0]['name']
    
    def _record_service_success(self, service_name: str, solve_time: float):
        """Record successful captcha solve"""
        stats = self.service_stats[service_name]
        stats['successes'] += 1
        stats['last_success'] = time.time()
        
        # Update average solve time
        total_attempts = stats['successes'] + stats['failures']
        stats['avg_solve_time'] = (stats['avg_solve_time'] * (total_attempts - 1) + solve_time) / total_attempts
    
    def _record_service_failure(self, service_name: str):
        """Record failed captcha solve"""
        self.service_stats[service_name]['failures'] += 1
    
    def get_service_stats(self) -> Dict[str, Dict]:
        """Get statistics for all services"""
        return self.service_stats.copy()

class BaseCaptchaService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def supports_captcha_type(self, captcha_type: CaptchaType) -> bool:
        """Check if service supports the given captcha type"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if service is available (has API key, etc.)"""
        return bool(self.api_key)
    
    async def solve(self, captcha_type: CaptchaType, **kwargs) -> Dict[str, Any]:
        """Solve captcha"""
        raise NotImplementedError

class TwoCaptchaService(BaseCaptchaService):
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "http://2captcha.com"
        self.supported_types = {
            CaptchaType.IMAGE,
            CaptchaType.RECAPTCHA_V2,
            CaptchaType.RECAPTCHA_V3,
            CaptchaType.HCAPTCHA,
            CaptchaType.FUNCAPTCHA,
            CaptchaType.GEETEST
        }
    
    def supports_captcha_type(self, captcha_type: CaptchaType) -> bool:
        return captcha_type in self.supported_types
    
    async def solve(self, captcha_type: CaptchaType, **kwargs) -> Dict[str, Any]:
        if captcha_type == CaptchaType.IMAGE:
            return await self._solve_image_captcha(**kwargs)
        elif captcha_type == CaptchaType.RECAPTCHA_V2:
            return await self._solve_recaptcha_v2(**kwargs)
        elif captcha_type == CaptchaType.HCAPTCHA:
            return await self._solve_hcaptcha(**kwargs)
        else:
            return {'success': False, 'error': f'Unsupported captcha type: {captcha_type}'}
    
    async def _solve_image_captcha(self, image_data: bytes, **kwargs) -> Dict[str, Any]:
        """Solve image captcha"""
        try:
            # Submit captcha
            submit_data = {
                'method': 'base64',
                'key': self.api_key,
                'body': base64.b64encode(image_data).decode()
            }
            
            response = requests.post(f"{self.base_url}/in.php", data=submit_data, timeout=30)
            if not response.text.startswith('OK|'):
                return {'success': False, 'error': response.text}
            
            captcha_id = response.text.split('|')[1]
            
            # Poll for result
            for attempt in range(30):  # Wait up to 5 minutes
                await asyncio.sleep(10)
                
                result_response = requests.get(
                    f"{self.base_url}/res.php",
                    params={'key': self.api_key, 'action': 'get', 'id': captcha_id},
                    timeout=30
                )
                
                if result_response.text == 'CAPCHA_NOT_READY':
                    continue
                elif result_response.text.startswith('OK|'):
                    return {'success': True, 'solution': result_response.text.split('|')[1]}
                else:
                    return {'success': False, 'error': result_response.text}
            
            return {'success': False, 'error': 'Timeout waiting for solution'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _solve_recaptcha_v2(self, sitekey: str, page_url: str, **kwargs) -> Dict[str, Any]:
        """Solve reCAPTCHA v2"""
        try:
            submit_data = {
                'method': 'userrecaptcha',
                'key': self.api_key,
                'googlekey': sitekey,
                'pageurl': page_url
            }
            
            response = requests.post(f"{self.base_url}/in.php", data=submit_data, timeout=30)
            if not response.text.startswith('OK|'):
                return {'success': False, 'error': response.text}
            
            captcha_id = response.text.split('|')[1]
            
            # Poll for result
            for attempt in range(60):  # Wait up to 10 minutes for reCAPTCHA
                await asyncio.sleep(10)
                
                result_response = requests.get(
                    f"{self.base_url}/res.php",
                    params={'key': self.api_key, 'action': 'get', 'id': captcha_id},
                    timeout=30
                )
                
                if result_response.text == 'CAPCHA_NOT_READY':
                    continue
                elif result_response.text.startswith('OK|'):
                    return {'success': True, 'solution': result_response.text.split('|')[1]}
                else:
                    return {'success': False, 'error': result_response.text}
            
            return {'success': False, 'error': 'Timeout waiting for reCAPTCHA solution'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _solve_hcaptcha(self, sitekey: str, page_url: str, **kwargs) -> Dict[str, Any]:
        """Solve hCaptcha"""
        try:
            submit_data = {
                'method': 'hcaptcha',
                'key': self.api_key,
                'sitekey': sitekey,
                'pageurl': page_url
            }
            
            response = requests.post(f"{self.base_url}/in.php", data=submit_data, timeout=30)
            if not response.text.startswith('OK|'):
                return {'success': False, 'error': response.text}
            
            captcha_id = response.text.split('|')[1]
            
            # Poll for result
            for attempt in range(60):
                await asyncio.sleep(10)
                
                result_response = requests.get(
                    f"{self.base_url}/res.php",
                    params={'key': self.api_key, 'action': 'get', 'id': captcha_id},
                    timeout=30
                )
                
                if result_response.text == 'CAPCHA_NOT_READY':
                    continue
                elif result_response.text.startswith('OK|'):
                    return {'success': True, 'solution': result_response.text.split('|')[1]}
                else:
                    return {'success': False, 'error': result_response.text}
            
            return {'success': False, 'error': 'Timeout waiting for hCaptcha solution'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

class AntiCaptchaService(BaseCaptchaService):
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.anti-captcha.com"
        self.supported_types = {
            CaptchaType.IMAGE,
            CaptchaType.RECAPTCHA_V2,
            CaptchaType.RECAPTCHA_V3,
            CaptchaType.HCAPTCHA,
            CaptchaType.FUNCAPTCHA
        }
    
    def supports_captcha_type(self, captcha_type: CaptchaType) -> bool:
        return captcha_type in self.supported_types
    
    async def solve(self, captcha_type: CaptchaType, **kwargs) -> Dict[str, Any]:
        # Implementation for AntiCaptcha service
        return {'success': False, 'error': 'AntiCaptcha service not implemented yet'}

class DeathByCaptchaService(BaseCaptchaService):
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "http://api.dbcapi.me/api"
        self.supported_types = {CaptchaType.IMAGE, CaptchaType.RECAPTCHA_V2}
    
    def supports_captcha_type(self, captcha_type: CaptchaType) -> bool:
        return captcha_type in self.supported_types
    
    async def solve(self, captcha_type: CaptchaType, **kwargs) -> Dict[str, Any]:
        # Implementation for DeathByCaptcha service
        return {'success': False, 'error': 'DeathByCaptcha service not implemented yet'}

class CapMonsterService(BaseCaptchaService):
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.base_url = "https://api.capmonster.cloud"
        self.supported_types = {
            CaptchaType.IMAGE,
            CaptchaType.RECAPTCHA_V2,
            CaptchaType.RECAPTCHA_V3,
            CaptchaType.HCAPTCHA
        }
    
    def supports_captcha_type(self, captcha_type: CaptchaType) -> bool:
        return captcha_type in self.supported_types
    
    async def solve(self, captcha_type: CaptchaType, **kwargs) -> Dict[str, Any]:
        # Implementation for CapMonster service
        return {'success': False, 'error': 'CapMonster service not implemented yet'}