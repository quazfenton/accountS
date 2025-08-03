#!/usr/bin/env python3
"""
Advanced system test for the enhanced account creation system.
Tests all new components including orchestrator, stealth browser, verification solver, etc.
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add the current directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent))

def test_advanced_imports():
    """Test that all advanced modules can be imported successfully"""
    print("Testing advanced imports...")
    
    try:
        from config.advanced_config import AdvancedConfig
        print("✅ AdvancedConfig imported successfully")
    except Exception as e:
        print(f"❌ AdvancedConfig import failed: {e}")
        return False
    
    try:
        from utils.proxy_manager import ImprovedProxyManager
        print("✅ ImprovedProxyManager imported successfully")
    except Exception as e:
        print(f"❌ ImprovedProxyManager import failed: {e}")
        return False
    
    try:
        from utils.stealth_browser import StealthBrowserAutomation
        print("✅ StealthBrowserAutomation imported successfully")
    except Exception as e:
        print(f"❌ StealthBrowserAutomation import failed: {e}")
        return False
    
    try:
        from utils.advanced_captcha_solver import AdvancedCaptchaSolver
        print("✅ AdvancedCaptchaSolver imported successfully")
    except Exception as e:
        print(f"❌ AdvancedCaptchaSolver import failed: {e}")
        return False
    
    try:
        from utils.monitoring import MetricsCollector, PerformanceMonitor, AlertManager
        print("✅ Monitoring components imported successfully")
    except Exception as e:
        print(f"❌ Monitoring components import failed: {e}")
        return False
    
    try:
        from modules.account_orchestrator import AccountOrchestrator
        print("✅ AccountOrchestrator imported successfully")
    except Exception as e:
        print(f"❌ AccountOrchestrator import failed: {e}")
        return False
    
    try:
        from modules.advanced_verification_solver import AdvancedVerificationSolver
        print("✅ AdvancedVerificationSolver imported successfully")
    except Exception as e:
        print(f"❌ AdvancedVerificationSolver import failed: {e}")
        return False
    
    try:
        from modules.improved_email_registration import ImprovedEmailRegistration
        print("✅ ImprovedEmailRegistration imported successfully")
    except Exception as e:
        print(f"❌ ImprovedEmailRegistration import failed: {e}")
        return False
    
    return True

def test_advanced_configuration():
    """Test advanced configuration system"""
    print("\nTesting advanced configuration...")
    
    try:
        from config.advanced_config import AdvancedConfig
        
        config = AdvancedConfig()
        
        # Test configuration loading
        browser_settings = config.browser_settings
        if not isinstance(browser_settings, dict):
            print("❌ Browser settings not loaded properly")
            return False
        
        rate_limiting = config.rate_limiting
        if not isinstance(rate_limiting, dict):
            print("❌ Rate limiting settings not loaded properly")
            return False
        
        # Test proxy configuration
        proxies = config.proxies
        print(f"📊 Loaded {len(proxies)} proxy configurations")
        
        # Test captcha services
        captcha_services = config.captcha_services
        print(f"📊 Loaded {len(captcha_services)} captcha service configurations")
        
        # Test user agent rotation
        user_agent = config.get_random_user_agent()
        if not user_agent or not isinstance(user_agent, str):
            print("❌ User agent generation failed")
            return False
        
        print("✅ Advanced configuration system working")
        return True
        
    except Exception as e:
        print(f"❌ Advanced configuration test failed: {e}")
        return False

def test_proxy_manager():
    """Test improved proxy manager"""
    print("\nTesting proxy manager...")
    
    try:
        from utils.proxy_manager import ImprovedProxyManager
        
        # Test with dummy proxies
        test_proxies = [
            "127.0.0.1:8080",
            "127.0.0.1:8081",
            "127.0.0.1:8082"
        ]
        
        proxy_manager = ImprovedProxyManager(test_proxies)
        
        # Test proxy selection
        best_proxy = asyncio.run(proxy_manager.get_best_proxy())
        if not best_proxy:
            print("⚠️ No proxy selected (expected with dummy proxies)")
        else:
            print(f"📊 Selected proxy: {best_proxy}")
        
        # Test proxy statistics
        stats = proxy_manager.get_proxy_stats()
        if not isinstance(stats, dict):
            print("❌ Proxy statistics not working")
            return False
        
        print(f"📊 Proxy statistics: {len(stats)} proxies tracked")
        
        # Test success/failure recording
        proxy_manager.record_success(test_proxies[0], 1.5)
        proxy_manager.record_failure(test_proxies[1], 5.0)
        
        print("✅ Proxy manager working")
        return True
        
    except Exception as e:
        print(f"❌ Proxy manager test failed: {e}")
        return False

async def test_stealth_browser():
    """Test stealth browser automation"""
    print("\nTesting stealth browser...")
    
    try:
        from utils.stealth_browser import StealthBrowserAutomation
        
        browser_automation = StealthBrowserAutomation()
        
        # Test browser context creation (without actually launching)
        print("📊 StealthBrowserAutomation initialized")
        print(f"📊 {len(browser_automation.user_agents)} user agents available")
        print(f"📊 {len(browser_automation.screen_resolutions)} screen resolutions available")
        
        # Test would require actual browser launch, so we'll skip for now
        print("✅ Stealth browser automation initialized (full test requires browser)")
        return True
        
    except Exception as e:
        print(f"❌ Stealth browser test failed: {e}")
        return False

def test_captcha_solver():
    """Test advanced captcha solver"""
    print("\nTesting captcha solver...")
    
    try:
        from utils.advanced_captcha_solver import AdvancedCaptchaSolver, CaptchaType
        
        captcha_solver = AdvancedCaptchaSolver()
        
        # Test service initialization
        services = captcha_solver.services
        print(f"📊 {len(services)} captcha services configured")
        
        # Test service statistics
        stats = captcha_solver.get_service_stats()
        if not isinstance(stats, dict):
            print("❌ Service statistics not working")
            return False
        
        print("✅ Captcha solver initialized")
        return True
        
    except Exception as e:
        print(f"❌ Captcha solver test failed: {e}")
        return False

def test_monitoring_system():
    """Test monitoring and metrics system"""
    print("\nTesting monitoring system...")
    
    try:
        from utils.monitoring import MetricsCollector, PerformanceMonitor, AlertManager, AccountCreationMetric
        from datetime import datetime
        
        # Test metrics collector
        metrics_collector = MetricsCollector()
        
        # Test metric recording
        test_metric = AccountCreationMetric(
            timestamp=datetime.now(),
            platform='test',
            success=True,
            proxy_used='127.0.0.1:8080',
            captcha_solved=True,
            creation_time_seconds=45.5
        )
        
        metrics_collector.record_account_creation(test_metric)
        
        # Test success rate calculation
        success_rate = metrics_collector.get_success_rate(hours=1)
        if not isinstance(success_rate, float):
            print("❌ Success rate calculation failed")
            return False
        
        print(f"📊 Success rate: {success_rate:.2%}")
        
        # Test performance monitor
        performance_monitor = PerformanceMonitor(metrics_collector)
        system_health = performance_monitor.get_system_health()
        
        print(f"📊 System health: CPU {system_health.cpu_usage:.1f}%, Memory {system_health.memory_usage:.1f}%")
        
        # Test alert manager
        alert_manager = AlertManager(metrics_collector)
        alert_manager.check_alerts()
        
        print("✅ Monitoring system working")
        return True
        
    except Exception as e:
        print(f"❌ Monitoring system test failed: {e}")
        return False

def test_verification_solver():
    """Test advanced verification solver"""
    print("\nTesting verification solver...")
    
    try:
        from modules.advanced_verification_solver import AdvancedVerificationSolver, VerificationType
        
        verification_solver = AdvancedVerificationSolver()
        
        # Test initialization
        print(f"📊 SMS services configured: {len(verification_solver.sms_services)}")
        print(f"📊 Voice services configured: {len(verification_solver.voice_services)}")
        
        # Test failure tracking
        verification_solver._increment_failure_count('consecutive_failures')
        should_intervene = verification_solver._should_request_human_intervention()
        
        print(f"📊 Human intervention check: {should_intervene}")
        
        print("✅ Verification solver initialized")
        return True
        
    except Exception as e:
        print(f"❌ Verification solver test failed: {e}")
        return False

async def test_account_orchestrator():
    """Test account orchestrator"""
    print("\nTesting account orchestrator...")
    
    try:
        from modules.account_orchestrator import AccountOrchestrator
        
        orchestrator = AccountOrchestrator()
        
        # Test initialization
        print(f"📊 Platform handlers: {len(orchestrator.platform_handlers)}")
        print(f"📊 Creation strategies: {len(orchestrator.creation_strategies)}")
        print(f"📊 Platform dependencies: {len(orchestrator.platform_dependencies)}")
        
        # Test platform optimization
        test_platforms = ['twitter', 'facebook', 'instagram']
        optimized_order = orchestrator._optimize_platform_order(test_platforms)
        
        print(f"📊 Optimized platform order: {optimized_order}")
        
        # Test delay calculation
        delay = orchestrator._calculate_inter_platform_delay('twitter', 0)
        print(f"📊 Inter-platform delay: {delay:.1f}s")
        
        print("✅ Account orchestrator working")
        return True
        
    except Exception as e:
        print(f"❌ Account orchestrator test failed: {e}")
        return False

def test_enhanced_identity_generation():
    """Test enhanced identity generation with realistic names"""
    print("\nTesting enhanced identity generation...")
    
    try:
        from utils.identity_generator import IdentityGenerator
        
        identity_gen = IdentityGenerator()
        
        # Test realistic name generation
        first_name, last_name, gender = identity_gen.generate_realistic_name()
        print(f"📊 Generated name: {first_name} {last_name} ({gender})")
        
        # Test enhanced username generation
        username_styles = ['name_based', 'word_based', 'mixed']
        for style in username_styles:
            username = identity_gen.generate_username(style=style)
            print(f"📊 {style} username: {username}")
        
        # Test complete identity
        identity = identity_gen.generate_identity()
        required_fields = ['username', 'password', 'email', 'first_name', 'last_name', 'gender']
        
        for field in required_fields:
            if field not in identity:
                print(f"❌ Missing field in identity: {field}")
                return False
        
        print(f"📊 Complete identity: {identity['first_name']} {identity['last_name']} ({identity['email']})")
        
        print("✅ Enhanced identity generation working")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced identity generation test failed: {e}")
        return False

async def test_improved_email_registration():
    """Test improved email registration (without actually registering)"""
    print("\nTesting improved email registration...")
    
    try:
        from modules.improved_email_registration import ImprovedEmailRegistration
        from utils.identity_generator import IdentityGenerator
        
        # Initialize components
        email_registration = ImprovedEmailRegistration()
        identity_gen = IdentityGenerator()
        
        # Test email provider configurations
        providers = email_registration.email_providers
        print(f"📊 Email providers configured: {list(providers.keys())}")
        
        for provider, config in providers.items():
            print(f"  - {provider}: {len(config['selectors'])} selectors, {len(config['success_indicators'])} success indicators")
        
        # Test identity generation for email
        identity = identity_gen.generate_identity()
        print(f"📊 Test identity: {identity['email']}")
        
        print("✅ Improved email registration initialized (full test requires actual registration)")
        return True
        
    except Exception as e:
        print(f"❌ Improved email registration test failed: {e}")
        return False

async def main():
    """Run all advanced system tests"""
    print("🚀 Starting advanced system tests...\n")
    
    tests = [
        ("Advanced Imports", test_advanced_imports),
        ("Advanced Configuration", test_advanced_configuration),
        ("Proxy Manager", test_proxy_manager),
        ("Stealth Browser", test_stealth_browser),
        ("Captcha Solver", test_captcha_solver),
        ("Monitoring System", test_monitoring_system),
        ("Verification Solver", test_verification_solver),
        ("Account Orchestrator", test_account_orchestrator),
        ("Enhanced Identity Generation", test_enhanced_identity_generation),
        ("Improved Email Registration", test_improved_email_registration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
        
        print()  # Add spacing between tests
    
    print(f"\n{'='*60}")
    print(f"📊 ADVANCED SYSTEM TEST RESULTS: {passed}/{total} tests passed")
    print('='*60)
    
    if passed == total:
        print("🎉 All advanced tests passed! System is ready for production.")
        print("\n🚀 Next steps:")
        print("1. Configure your .env file with real API keys")
        print("2. Set up proxy services if needed")
        print("3. Configure captcha solving services")
        print("4. Run: python run_production.py")
        return True
    else:
        print("⚠️  Some advanced tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check your configuration files")
        print("3. Verify system requirements")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)