# Production Account Creation System

A sophisticated, production-ready system for automated account creation across multiple platforms with advanced detection prevention, identity management, and profile generation capabilities.

## 🚀 Features

- **Multi-Platform Support**: Twitter, Facebook, Instagram
- **Advanced Detection Prevention**: Browser fingerprint spoofing, human-like behavior simulation
- **Identity Management**: Comprehensive profile generation with face synthesis
- **Database Integration**: Supabase for account storage and management
- **Proxy Support**: Rotating proxy support for IP diversity
- **Captcha Solving**: Integration with external captcha solving services
- **SMS Verification**: Automated SMS verification handling
- **Identity Traversal**: Advanced identity relationship mapping
- **Production Monitoring**: Comprehensive logging and error handling

## 📋 Prerequisites

- Python 3.8+
- Node.js (for Playwright browser installation)
- Supabase account (for database)
- External services (optional):
  - Captcha solving service
  - SMS verification service
  - Proxy service

## 🛠️ Installation

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd accountS
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Environment

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Supabase configuration (Required)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Email configuration
EMAIL_SIGNUP_URL=https://accounts.google.com/signup
EMAIL_DOMAIN=gmail.com

# Browser configuration
HEADLESS_MODE=true
DEBUG_MODE=false

# Optional services
PROXY_LIST=proxy1:port,proxy2:port
CAPTCHA_SOLVER_API_KEY=your_captcha_api_key
SMS_VERIFICATION_API_KEY=your_sms_api_key
```

### 4. Initialize Database

The system will automatically create the required database tables on first run.

## 🎯 Usage

### Quick Start

Run the system test to verify everything is working:

```bash
python test_system.py
```

### Basic Account Creation

Create a single account:

```bash
python main.py --accounts 1 --platforms twitter
```

### Advanced Usage

Create multiple accounts with threading:

```bash
python main.py --accounts 5 --threads 2 --platforms twitter facebook instagram
```

### Identity Traversal Demo

Demonstrate advanced identity relationship mapping:

```bash
python main.py --traverse-identities --traversal-depth 5 --traversal-strength medium
```

### Production Mode

Run with full monitoring and error handling:

```bash
python run_production.py
```

## 📊 Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--accounts` | Number of accounts to create | 1 |
| `--threads` | Number of parallel threads | 1 |
| `--platforms` | Platforms to register on | twitter |
| `--traverse-identities` | Enable identity traversal demo | False |
| `--traversal-depth` | Depth of identity traversal | 5 |
| `--traversal-strength` | Variation strength (low/medium/high) | medium |

## 🏗️ Architecture

### Core Components

1. **Email Registration** (`modules/email_registration.py`)
   - Automated email account creation
   - Advanced browser fingerprint spoofing
   - Human-like interaction simulation

2. **Social Media Registration** (`modules/social_media_registration.py`)
   - Multi-platform account creation
   - Captcha solving integration
   - SMS verification handling

3. **Profile Manager** (`modules/profile_manager.py`)
   - Comprehensive identity generation
   - Profile picture synthesis
   - Identity variation generation

4. **Database** (`modules/database.py`)
   - Supabase integration
   - Account storage and retrieval
   - Status tracking

5. **Detection Prevention** (`modules/detection_prevention.py`)
   - Browser fingerprint spoofing
   - WebGL, Canvas, Audio fingerprint randomization
   - Advanced stealth techniques

### Utilities

- **Identity Generator** (`utils/identity_generator.py`): Advanced username/password generation
- **Face Generator** (`utils/face_generator.py`): AI-powered profile picture generation
- **Notifier** (`utils/notifier.py`): Cross-platform notification system

## 🔧 Configuration

### Database Setup

1. Create a Supabase project
2. Get your project URL and API key
3. Update `.env` with your credentials
4. The system will automatically create required tables

### Proxy Configuration

Add proxies to your `.env` file:

```env
PROXY_LIST=proxy1.example.com:8080,proxy2.example.com:8080
```

### External Services

#### Captcha Solving

Configure a captcha solving service:

```env
CAPTCHA_SOLVER_API_KEY=your_api_key
CAPTCHA_SERVICE_URL=https://api.captchaservice.com/solve
```

#### SMS Verification

Configure SMS verification service:

```env
SMS_VERIFICATION_API_KEY=your_api_key
SMS_SERVICE_URL=https://api.sms-service.com
```

## 📈 Monitoring

### Logs

- `production.log`: Main application logs
- `failures.log`: Error and failure logs

### System Health

The production runner includes:
- Disk space monitoring
- Log file size monitoring
- Runtime statistics
- Automatic cleanup

## 🛡️ Security Features

- **Browser Fingerprint Spoofing**: Randomized WebGL, Canvas, Audio fingerprints
- **Human Behavior Simulation**: Realistic typing, mouse movement, scrolling
- **Proxy Rotation**: Automatic IP address rotation
- **Detection Evasion**: Advanced anti-detection techniques
- **Secure Storage**: Encrypted credential storage

## 🔍 Troubleshooting

### Common Issues

1. **Playwright Installation**
   ```bash
   playwright install chromium
   ```

2. **Database Connection**
   - Verify Supabase credentials
   - Check network connectivity
   - Ensure database permissions

3. **Browser Issues**
   - Install system dependencies for headless browsers
   - Check proxy configuration
   - Verify browser arguments

### Debug Mode

Enable debug mode for detailed logging:

```env
DEBUG_MODE=true
HEADLESS_MODE=false
```

## 📝 Development

### Running Tests

```bash
python test_system.py
```

### Adding New Platforms

1. Extend `SocialMediaRegistration` class
2. Add platform-specific registration method
3. Update configuration and documentation

### Custom Identity Generation

Modify `IdentityGenerator` and `ProfileManager` classes to customize identity generation logic.

## 🚨 Important Notes

### Legal Compliance

- Ensure compliance with platform Terms of Service
- Respect rate limits and usage policies
- Use responsibly and ethically

### Production Considerations

- Monitor resource usage
- Implement proper error handling
- Use secure credential storage
- Regular system maintenance

### Performance Optimization

- Adjust thread count based on system resources
- Monitor memory usage with large account batches
- Optimize proxy rotation for best performance

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review system logs
3. Test individual components
4. Verify configuration settings

## 🔄 Updates

Keep the system updated:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
playwright install chromium
```

---

**⚠️ Disclaimer**: This system is for educational and research purposes. Users are responsible for ensuring compliance with applicable laws and platform terms of service.