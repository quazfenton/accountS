#!/usr/bin/env python3
"""
Comprehensive test for the improved account creation system.
Tests the new ImprovedAccountManager, ImprovedDatabase, and platform handlers.
"""

import sys
import os
import asyncio
import time
import json
from pathlib import Path

# Add the current directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent))

def test_improved_database():
    """Test the improved database system"""
    print("Testing improved database...")
    
    try:
        from modules.improved_database import ImprovedDatabase, AccountRecord, ProxyStats, OperationLog
        
        # Initialize database
        db = ImprovedDatabase("test_accounts.db")
        
        # Test account saving
        test_account = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'platform': 'test_platform',
            'username': 'testuser',
            'profile': {'first_name': 'Test', 'last_name': 'User'},
            'verification_status': 'verified'
        }
        
        success = db.save_account(test_account)
        if not success:
            print("❌ Failed to save test account")
            return False
        
        print("✅ Account saved successfully")
        
        # Test account retrieval
        accounts = db.get_accounts(platform='test_platform')
        if not accounts or len(accounts) == 0:
            print("❌ Failed to retrieve accounts")
            return False
        
        print(f"✅ Retrieved {len(accounts)} accounts")
        
        # Test operation logging
        success = db.log_operation(
            operation_type='test',
            platform='test_platform',
            success=True,
            duration=1.5,
            account_email='test@example.com'
        )
        
        if not success:
            print("❌ Failed to log operation")
            return False
        
        print("✅ Operation logged successfully")
        
        # Test statistics
        stats = db.get_success_statistics(hours=1)
        if not isinstance(stats, dict):
            print("❌ Failed to get statistics")
            return False
        
        print(f"✅ Statistics retrieved: {stats.get('overall', {}).get('total_attempts', 0)} attempts")
        
        # Test proxy stats
        db.update_proxy_stats('127.0.0.1:8080', True, 1.2)
        proxy_stats = db.get_proxy_stats()
        
        if not isinstance(proxy_stats, list):
            print("❌ Failed to get proxy statistics")
            return False
        
        print(f"✅ Proxy statistics retrieved: {len(proxy_stats)} proxies")
        
        # Test database stats
        db_stats = db.get_database_stats()
        if not isinstance(db_stats, dict):
            print("❌ Failed to get database statistics")
            return False
        
        print(f"✅ Database statistics: {db_stats.get('accounts_count', 0)} accounts")
        
        # Cleanup
        db.close()
        if os.path.exists("test_accounts.db"):
            os.remove("test_accounts.db")
        
        print("✅ Improved database test passed")
        return True
        
    except Exception as e:
        print(f"❌ Improved database test failed: {e}")
        return False

def test_platform_handlers():
    """Test platform-specific handlers"""
    print("\nTesting platform handlers...")
    
    try:
        from modules.platform_handlers import PlatformHandlerFactory, TwitterHandler, FacebookHandler, InstagramHandler
        
        # Test factory
        supported_platforms = PlatformHandlerFactory.get_supported_platforms()
        print(f"📊 Supported platforms: {supported_platforms}")
        
        if len(supported_platforms) == 0:
            print("❌ No supported platforms found")
            return False
        
        # Test handler creation
        for platform in supported_platforms:
            try:
                handler = PlatformHandlerFactory.create_handler(platform)
                print(f"✅ {platform} handler created successfully")
                
                # Test handler configuration
                config = handler.config
                if not config.name or not config.signup_url:
                    print(f"❌ {platform} handler has invalid configuration")
                    return False
                
                print(f"  - Signup URL: {config.signup_url}")
                print(f"  - Selectors: {len(config.selectors)}")
                print(f"  - Success indicators: {len(config.success_indicators)}")
                print(f"  - Verification types: {len(config.verification_types)}")
                
                # Test statistics
                stats = handler.get_stats()
                if not isinstance(stats, dict):
                    print(f"❌ {platform} handler stats invalid")
                    return False
                
                print(f"  - Initial stats: {stats['attempts']} attempts")
                
            except Exception as e:
                print(f"❌ Failed to create {platform} handler: {e}")
                return False
        
        print("✅ Platform handlers test passed")
        return True
        
    except Exception as e:
        print(f"❌ Platform handlers test failed: {e}")
        return False

async def test_improved_account_manager():
    """Test the improved account manager"""
    print("\nTesting improved account manager...")
    
    try:
        from modules.improved_account_manager import ImprovedAccountManager
        from utils.identity_generator import IdentityGenerator
        
        # Initialize components
        identity_gen = IdentityGenerator()
        
        # Create account manager (without proxies for testing)
        account_manager = ImprovedAccountManager(
            proxy_list=None,
            max_workers=2,
            db_path="test_manager.db"
        )
        
        print("✅ Account manager initialized")
        
        # Test identity generation
        identity = identity_gen.generate_identity()
        required_fields = ['email', 'password', 'first_name', 'last_name', 'username']
        
        for field in required_fields:
            if field not in identity:
                print(f"❌ Missing field in identity: {field}")
                return False
        
        print(f"✅ Identity generated: {identity['email']}")
        
        # Test session statistics
        session_stats = account_manager.get_session_statistics()
        if not isinstance(session_stats, dict):
            print("❌ Failed to get session statistics")
            return False
        
        print(f"✅ Session statistics: {session_stats['total_attempts']} attempts")
        
        # Test database statistics
        db_stats = account_manager.get_database_statistics()
        if not isinstance(db_stats, dict):
            print("❌ Failed to get database statistics")
            return False
        
        print("✅ Database statistics retrieved")
        
        # Test health check
        health = await account_manager.health_check()
        if not isinstance(health, dict) or 'overall_status' not in health:
            print("❌ Health check failed")
            return False
        
        print(f"✅ Health check: {health['overall_status']}")
        
        # Test performance optimization
        optimization = await account_manager.optimize_performance()
        if not isinstance(optimization, dict):
            print("❌ Performance optimization failed")
            return False
        
        print(f"✅ Performance optimization: {len(optimization.get('optimizations_applied', []))} optimizations")
        
        # Test account export
        export_data = account_manager.export_accounts(format='json')
        if not isinstance(export_data, str):
            print("❌ Account export failed")
            return False
        
        print("✅ Account export successful")
        
        # Cleanup
        account_manager.shutdown()
        if os.path.exists("test_manager.db"):
            os.remove("test_manager.db")
        
        print("✅ Improved account manager test passed")
        return True
        
    except Exception as e:
        print(f"❌ Improved account manager test failed: {e}")
        return False

def test_identity_generation():
    """Test enhanced identity generation"""
    print("\nTesting enhanced identity generation...")
    
    try:
        from utils.identity_generator import IdentityGenerator
        
        identity_gen = IdentityGenerator()
        
        # Test realistic name generation
        first_name, last_name, gender = identity_gen.generate_realistic_name()
        
        if not first_name or not last_name or gender not in ['M', 'F']:
            print("❌ Invalid realistic name generation")
            return False
        
        print(f"✅ Realistic name: {first_name} {last_name} ({gender})")
        
        # Test different username styles
        username_styles = ['name_based', 'word_based', 'mixed']
        for style in username_styles:
            username = identity_gen.generate_username(style=style)
            if not username or len(username) < 3:
                print(f"❌ Invalid username for style {style}")
                return False
            print(f"✅ {style} username: {username}")
        
        # Test complete identity generation
        for i in range(3):
            identity = identity_gen.generate_identity()
            
            required_fields = ['username', 'password', 'email', 'first_name', 'last_name', 'gender']
            for field in required_fields:
                if field not in identity or not identity[field]:
                    print(f"❌ Missing or empty field: {field}")
                    return False
            
            print(f"✅ Complete identity {i+1}: {identity['first_name']} {identity['last_name']} ({identity['email']})")
        
        # Test seeded generation (should be consistent)
        identity_gen.set_seed(12345)
        identity1 = identity_gen.generate_identity()
        
        identity_gen.set_seed(12345)
        identity2 = identity_gen.generate_identity()
        
        if identity1['email'] != identity2['email']:
            print("❌ Seeded generation not consistent")
            return False
        
        print("✅ Seeded generation is consistent")
        
        print("✅ Enhanced identity generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced identity generation test failed: {e}")
        return False

def test_configuration_system():
    """Test configuration management"""
    print("\nTesting configuration system...")
    
    try:
        # Test basic config
        from config.config import Config
        
        basic_config = Config()
        
        # Check required attributes
        required_attrs = ['HEADLESS_MODE', 'DEBUG_MODE']
        for attr in required_attrs:
            if not hasattr(basic_config, attr):
                print(f"❌ Missing basic config attribute: {attr}")
                return False
        
        print("✅ Basic configuration loaded")
        
        # Test advanced config (may not exist)
        try:
            from config.advanced_config import AdvancedConfig
            
            advanced_config = AdvancedConfig()
            
            # Test configuration methods
            user_agent = advanced_config.get_random_user_agent()
            if not user_agent:
                print("❌ Failed to get random user agent")
                return False
            
            print(f"✅ Advanced configuration loaded, user agent: {user_agent[:50]}...")
            
            # Test proxy configuration
            proxies = advanced_config.proxies
            print(f"✅ Proxy configuration: {len(proxies)} proxies")
            
            # Test captcha services
            captcha_services = advanced_config.captcha_services
            print(f"✅ Captcha services: {len(captcha_services)} services")
            
        except Exception as e:
            print(f"⚠️ Advanced configuration not available: {e}")
        
        print("✅ Configuration system test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration system test failed: {e}")
        return False

def test_monitoring_system():
    """Test monitoring and metrics system"""
    print("\nTesting monitoring system...")
    
    try:
        from utils.monitoring import MetricsCollector, PerformanceMonitor, AlertManager, AccountCreationMetric
        from datetime import datetime
        
        # Test metrics collector
        metrics_collector = MetricsCollector()
        
        # Create test metrics
        test_metrics = [
            AccountCreationMetric(
                timestamp=datetime.now(),
                platform='test',
                success=True,
                proxy_used='127.0.0.1:8080',
                captcha_solved=True,
                creation_time_seconds=45.5
            ),
            AccountCreationMetric(
                timestamp=datetime.now(),
                platform='test',
                success=False,
                error_type='timeout',
                creation_time_seconds=120.0
            )
        ]
        
        # Record metrics
        for metric in test_metrics:
            metrics_collector.record_account_creation(metric)
        
        # Test success rate calculation
        success_rate = metrics_collector.get_success_rate(hours=1)
        if not isinstance(success_rate, float) or success_rate < 0 or success_rate > 1:
            print("❌ Invalid success rate calculation")
            return False
        
        print(f"✅ Success rate calculated: {success_rate:.2%}")
        
        # Test performance monitor
        performance_monitor = PerformanceMonitor(metrics_collector)
        system_health = performance_monitor.get_system_health()
        
        if not hasattr(system_health, 'cpu_usage') or not hasattr(system_health, 'memory_usage'):
            print("❌ Invalid system health data")
            return False
        
        print(f"✅ System health: CPU {system_health.cpu_usage:.1f}%, Memory {system_health.memory_usage:.1f}%")
        
        # Test alert manager
        alert_manager = AlertManager(metrics_collector)
        alert_manager.check_alerts()
        
        print("✅ Alert manager functioning")
        
        print("✅ Monitoring system test passed")
        return True
        
    except Exception as e:
        print(f"❌ Monitoring system test failed: {e}")
        return False

async def test_integration():
    """Test integration between components"""
    print("\nTesting component integration...")
    
    try:
        from modules.improved_account_manager import ImprovedAccountManager
        from utils.identity_generator import IdentityGenerator
        
        # Create minimal test setup
        identity_gen = IdentityGenerator()
        account_manager = ImprovedAccountManager(
            proxy_list=None,
            max_workers=1,
            db_path="test_integration.db"
        )
        
        # Generate test identity
        identity = identity_gen.generate_identity()
        
        print(f"✅ Integration test setup complete")
        print(f"📧 Test identity: {identity['email']}")
        
        # Test that components can work together
        session_stats = account_manager.get_session_statistics()
        health_check = await account_manager.health_check()
        
        if not session_stats or not health_check:
            print("❌ Component integration failed")
            return False
        
        print("✅ Components integrated successfully")
        
        # Cleanup
        account_manager.shutdown()
        if os.path.exists("test_integration.db"):
            os.remove("test_integration.db")
        
        print("✅ Integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Run all improved system tests"""
    print("🚀 Starting improved system tests...\n")
    
    tests = [
        ("Improved Database", test_improved_database),
        ("Platform Handlers", test_platform_handlers),
        ("Improved Account Manager", test_improved_account_manager),
        ("Enhanced Identity Generation", test_identity_generation),
        ("Configuration System", test_configuration_system),
        ("Monitoring System", test_monitoring_system),
        ("Component Integration", test_integration)
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
    print(f"📊 IMPROVED SYSTEM TEST RESULTS: {passed}/{total} tests passed")
    print('='*60)
    
    if passed == total:
        print("🎉 All improved system tests passed! System is ready for production.")
        print("\n🚀 Next steps:")
        print("1. Configure your .env file with real credentials")
        print("2. Set up external services (proxies, captcha solvers)")
        print("3. Run: python main.py --accounts 1 --platforms twitter")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure all dependencies are installed")
        print("2. Check file permissions")
        print("3. Verify system requirements")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)