from interfaces.verification_service import AbstractVerificationService, VerificationResult
from utils.advanced_captcha_solver import AdvancedCaptchaSolver
import asyncio
import logging
import imaplib
import email as email_lib
import re
import time
from datetime import datetime, timedelta
from email.header import decode_header

class ConcreteVerificationService(AbstractVerificationService):
    """Concrete implementation of verification service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.captcha_solver = AdvancedCaptchaSolver()
    
    async def verify_email(self, email: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Implement email verification"""
        try:
            # Use method to get email verification code
            code_result = await self._get_email_verification_code(email, verification_context.get('timeout', 300))
            
            if code_result['success']:
                return VerificationResult(
                    success=True,
                    verification_code=code_result['code']
                )
            else:
                return VerificationResult(
                    success=False,
                    error_message=code_result['error']
                )
        except Exception as e:
            self.logger.error(f"Email verification error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def verify_sms(self, phone_number: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Implement SMS verification"""
        try:
            # Implementation for SMS verification
            # This would involve getting phone number, requesting code, etc.
            # Placeholder for actual implementation
            return VerificationResult(
                success=False,
                error_message="SMS verification not fully implemented"
            )
        except Exception as e:
            self.logger.error(f"SMS verification error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def solve_captcha(self, captcha_type: str, captcha_context: Dict[str, Any]) -> VerificationResult:
        """Implement captcha solving"""
        try:
            # Use existing captcha solver
            result = await self.captcha_solver.solve_captcha(captcha_type, **captcha_context)
            
            if result['success']:
                return VerificationResult(
                    success=True,
                    verification_code=result['solution']
                )
            else:
                return VerificationResult(
                    success=False,
                    error_message=result.get('error', 'Captcha solving failed')
                )
        except Exception as e:
            self.logger.error(f"Captcha solving error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def verify_2fa(self, method: str, verification_context: Dict[str, Any]) -> VerificationResult:
        """Implement 2FA verification"""
        try:
            # Implementation for 2FA verification based on method (TOTP, SMS, etc.)
            return VerificationResult(
                success=False,
                error_message="2FA verification not fully implemented"
            )
        except Exception as e:
            self.logger.error(f"2FA verification error: {e}")
            return VerificationResult(
                success=False,
                error_message=str(e)
            )
    
    async def _get_email_verification_code(self, email: str, timeout: int = 300) -> Dict[str, Any]:
        """Helper to get email verification code - to be implemented properly"""
        try:
            import imaplib
            import email as email_lib
            import re
            import time
            from datetime import datetime, timedelta
            from email.header import decode_header
            
            # Extract email configuration from advanced config
            from config.advanced_config import AdvancedConfig
            config = AdvancedConfig()
            email_config = config.data.get('email_verification', {})
            
            if not email_config.get('enabled', False):
                return {'success': False, 'error': 'Email verification not enabled in configuration'}
            
            # Extract email service and credentials from environment/config
            email_parts = email.split('@')
            if len(email_parts) != 2:
                return {'success': False, 'error': 'Invalid email format'}
            
            email_user = email_parts[0]
            email_domain = email_parts[1]
            
            # Map common email domains to their IMAP servers
            imap_servers = {
                'gmail.com': ('imap.gmail.com', 993),
                'outlook.com': ('outlook.office365.com', 993),
                'hotmail.com': ('outlook.office365.com', 993),
                'live.com': ('outlook.office365.com', 993),
                'yahoo.com': ('imap.mail.yahoo.com', 993),
                'icloud.com': ('imap.mail.me.com', 993),
            }
            
            if email_domain not in imap_servers:
                return {'success': False, 'error': f'Email provider {email_domain} not supported'}
            
            server, port = imap_servers[email_domain]
            
            # Get credentials from secure configuration (would be loaded from .env or config file)
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            username = os.getenv('EMAIL_USERNAME', email_config.get('username', ''))
            password = os.getenv('EMAIL_PASSWORD', email_config.get('password', ''))
            
            if not username or not password:
                return {'success': False, 'error': 'Email credentials not configured in environment'}
            
            # Connect to email server
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(username, password)
            mail.select('inbox')
            
            start_time = time.time()
            
            # Search for verification emails until timeout
            while time.time() - start_time < timeout:
                try:
                    # Search for recent emails (last 10 minutes)
                    since_date = (datetime.now() - timedelta(minutes=10)).strftime("%d-%b-%Y")
                    status, messages = mail.search(None, f'(SINCE {since_date})', f'(TO "{email}")')
                    
                    if status == 'OK':
                        email_ids = messages[0].split()
                        
                        # Process emails in reverse chronological order (newest first)
                        for email_id in reversed(email_ids):
                            status, msg_data = mail.fetch(email_id, '(RFC822)')
                            
                            if status == 'OK':
                                raw_email = msg_data[0][1]
                                msg = email_lib.message_from_bytes(raw_email)
                                
                                # Extract subject and sender
                                subject = self._decode_mime_words(msg.get('Subject', ''))
                                sender = msg.get('From', '')
                                
                                # Check if this is a verification email
                                is_verification = self._is_verification_email(subject, sender)
                                
                                if is_verification:
                                    # Extract email body
                                    body = self._extract_email_body(msg)
                                    
                                    # Look for verification code using multiple patterns
                                    code = self._extract_verification_code(body)
                                    
                                    if code:
                                        # Mark email as read
                                        mail.store(email_id, '+FLAGS', '\\Seen')
                                        mail.close()
                                        mail.logout()
                                        
                                        self.logger.info(f"Found verification code: {code}")
                                        return {
                                            'success': True,
                                            'code': code,
                                            'source': 'email_verification',
                                            'timestamp': datetime.now().isoformat()
                                        }
                
                except Exception as e:
                    self.logger.warning(f"Error processing emails: {e}")
                    # Continue waiting for emails
                
                # Wait before next check
                await asyncio.sleep(10)
            
            mail.close()
            mail.logout()
            return {'success': False, 'error': 'Verification code not found within timeout period'}
            
        except imaplib.IMAP4.error as e:
            self.logger.error(f"IMAP error: {e}")
            return {'success': False, 'error': f'IMAP connection error: {str(e)}'}
        except Exception as e:
            self.logger.error(f"Email verification error: {e}")
            return {'success': False, 'error': f'Email verification error: {str(e)}'}
    
    def _decode_mime_words(self, s):
        """Decode MIME encoded words in email headers"""
        decoded_fragments = decode_header(s)
        decoded_string = ''
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                if encoding:
                    decoded_string += fragment.decode(encoding)
                else:
                    decoded_string += fragment.decode('utf-8', errors='ignore')
            else:
                decoded_string += fragment
        return decoded_string

    def _is_verification_email(self, subject: str, sender: str) -> bool:
        """Check if an email is a verification email"""
        subject_lower = subject.lower()
        sender_lower = sender.lower()
        
        verification_keywords = [
            'verification', 'confirm', 'activate', 'verify', 'email verification',
            'account verification', 'verification code', 'confirm your account'
        ]
        
        verification_senders = [
            'noreply', 'no-reply', 'verification', 'confirm', 'support', 'admin'
        ]
        
        # Check subject for verification keywords
        has_verification_subject = any(keyword in subject_lower for keyword in verification_keywords)
        
        # Check sender for verification indicators
        has_verification_sender = any(sender_domain in sender_lower for sender_domain in verification_senders)
        
        return has_verification_subject or has_verification_sender

    def _extract_email_body(self, msg):
        """Extract text body from email message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except:
                        continue
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        html_body = part.get_payload(decode=True).decode('utf-8')
                        # Simple HTML to text conversion
                        import re
                        body = re.sub('<[^<]+?>', '', html_body)
                        break
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8')
            except:
                body = ""
        
        return body

    def _extract_verification_code(self, body: str) -> str:
        """Extract verification code from email body using various patterns"""
        # Common verification code patterns
        patterns = [
            # 4-8 digit codes
            r'(\d{4,8})',
            # Codes with spaces (like SMS verification)
            r'(\d{3,4}\s+\d{3,4})',
            # Codes with separators
            r'([A-Z0-9]{4,8}-[A-Z0-9]{4,8})',
            r'([A-Z0-9]{4,8})',  # Alpha-numeric codes
            # Codes with prefixes
            r'code[:\s]+([A-Z0-9]{4,8})',
            r'activation[:\s]+([A-Z0-9]{4,8})',
            r'verification[:\s]+([A-Z0-9]{4,8})',
            r'confirm[:\s]+([A-Z0-9]{4,8})',
            r'verify[:\s]+([A-Z0-9]{4,8})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                code = match.group(1).strip()
                # Remove spaces that were used for formatting
                code = code.replace(' ', '').replace('-', '')
                # Only return if it looks like a proper verification code
                if len(code) >= 4 and len(code) <= 10:
                    return code
        
        return None