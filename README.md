# Advanced Bot Account Management System

This system automates the creation of email accounts and corresponding social media accounts at scale, with advanced detection prevention and identity management.

## Features

- **Email Registration**: Automates email account creation with proxy rotation and captcha solving
- **Social Media Linking**: Registers accounts on Twitter, Facebook, and other platforms
- **Identity Generation**: Creates realistic identities with consistent profiles
- **Detection Prevention**: Implements browser fingerprint spoofing and other stealth techniques
- **Database Storage**: Stores credentials in Supabase database
- **Error Handling**: Automatic retries and human intervention notifications
- **Browserless Integration**: Supports headless browser automation via Browserless
- **Stagehand Compatibility**: Works with Stagehand for advanced automation workflows

## Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     - SUPABASE_URL and SUPABASE_KEY
     - EMAIL_API_KEY and EMAIL_DOMAIN
     - Social media API keys
     - BROWSERLESS_API_KEY (if using Browserless)
     - CAPTCHA_SERVICE_API_KEY (if using captcha solving service)

3. **Set up Supabase**:
   - Create a `bot_accounts` table with columns:
     - email (text)
     - email_password (text)
     - proxy (text)
     - social_credentials (json)
     - status (text)

## Usage

Run the main script:
```bash
python -m bot_account_manager.main
```

## Configuration Options

- `NUM_ACCOUNTS`: Number of accounts to create (set in main.py)
- `SOCIAL_PLATFORMS`: Platforms to register (set in main.py)

## Advanced Features

### Detection Prevention
The system includes comprehensive browser fingerprint spoofing:
- User agent rotation
- Canvas fingerprint spoofing
- WebGL spoofing
- WebRTC blocking

### Human Intervention
The system will send system notifications when:
- Email registration fails after retries
- Social media registration requires human intervention
- Captchas cannot be solved automatically

### Identity Management
The system generates identities with:
- Realistic usernames from word combinations
- Strong passwords with special characters
- Consistent personal information across platforms

## Troubleshooting

Check `failures.log` for detailed error information.

For Browserless integration issues, verify your API key and network connectivity.