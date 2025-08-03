#!/usr/bin/env python3
"""
Production startup script for the account creation system.
This script includes proper error handling, logging, and monitoring.
"""

import sys
import os
import time
import signal
import logging
from pathlib import Path
from datetime import datetime

# Add the current directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ProductionRunner:
    def __init__(self):
        self.running = True
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def check_dependencies(self):
        """Check that all required dependencies are available"""
        logger.info("Checking system dependencies...")
        
        try:
            import playwright
            logger.info("✅ Playwright available")
        except ImportError:
            logger.error("❌ Playwright not installed. Run: pip install playwright")
            return False
        
        try:
            import torch
            logger.info("✅ PyTorch available")
        except ImportError:
            logger.error("❌ PyTorch not installed. Run: pip install torch")
            return False
        
        try:
            from config.config import Config
            config = Config()
            
            # Check critical configuration
            if not config.SUPABASE_URL or not config.SUPABASE_KEY:
                logger.error("❌ Supabase configuration missing")
                return False
            
            if not config.EMAIL_SIGNUP_URL:
                logger.error("❌ Email signup URL not configured")
                return False
            
            logger.info("✅ Configuration validated")
            
        except Exception as e:
            logger.error(f"❌ Configuration error: {e}")
            return False
        
        return True
    
    def run_system_test(self):
        """Run system tests before starting production"""
        logger.info("Running system tests...")
        
        try:
            from test_system import main as run_tests
            if run_tests():
                logger.info("✅ All system tests passed")
                return True
            else:
                logger.error("❌ System tests failed")
                return False
        except Exception as e:
            logger.error(f"❌ System test error: {e}")
            return False
    
    def start_production(self, accounts=5, threads=2, platforms=['twitter']):
        """Start the production account creation process"""
        logger.info(f"Starting production run: {accounts} accounts, {threads} threads, platforms: {platforms}")
        
        try:
            from main import main as run_main
            
            # Override sys.argv to pass arguments to main
            original_argv = sys.argv.copy()
            sys.argv = [
                'main.py',
                '--accounts', str(accounts),
                '--threads', str(threads),
                '--platforms'] + platforms
            
            try:
                run_main()
                logger.info("✅ Production run completed successfully")
                return True
            finally:
                sys.argv = original_argv
                
        except KeyboardInterrupt:
            logger.info("Production run interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Production run failed: {e}")
            return False
    
    def monitor_system(self):
        """Monitor system health during operation"""
        logger.info("Starting system monitoring...")
        
        start_time = time.time()
        
        while self.running:
            try:
                # Check disk space
                disk_usage = os.statvfs('.')
                free_space_gb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024**3)
                
                if free_space_gb < 1.0:  # Less than 1GB free
                    logger.warning(f"Low disk space: {free_space_gb:.2f}GB remaining")
                
                # Check log file size
                if os.path.exists('production.log'):
                    log_size_mb = os.path.getsize('production.log') / (1024**2)
                    if log_size_mb > 100:  # Log file larger than 100MB
                        logger.warning(f"Large log file: {log_size_mb:.2f}MB")
                
                # Runtime statistics
                runtime_hours = (time.time() - start_time) / 3600
                if runtime_hours > 0 and int(runtime_hours) % 1 == 0:  # Every hour
                    logger.info(f"System running for {runtime_hours:.1f} hours")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)
    
    def cleanup(self):
        """Cleanup resources before shutdown"""
        logger.info("Performing cleanup...")
        
        try:
            # Clean up temporary files
            import glob
            temp_files = glob.glob('*.tmp') + glob.glob('temp_*')
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    logger.info(f"Removed temp file: {temp_file}")
                except:
                    pass
            
            # Archive old logs if they exist
            if os.path.exists('production.log'):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                archive_name = f'production_{timestamp}.log'
                os.rename('production.log', archive_name)
                logger.info(f"Archived log to: {archive_name}")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def main():
    """Main production entry point"""
    runner = ProductionRunner()
    
    try:
        logger.info("🚀 Starting production account creation system")
        
        # Step 1: Check dependencies
        if not runner.check_dependencies():
            logger.error("❌ Dependency check failed")
            return False
        
        # Step 2: Run system tests
        if not runner.run_system_test():
            logger.error("❌ System tests failed")
            return False
        
        # Step 3: Start production with default settings
        # You can modify these parameters as needed
        success = runner.start_production(
            accounts=3,  # Start with a small number for testing
            threads=1,   # Single thread for stability
            platforms=['twitter']  # Start with one platform
        )
        
        if success:
            logger.info("🎉 Production run completed successfully")
        else:
            logger.error("❌ Production run failed")
        
        return success
        
    except KeyboardInterrupt:
        logger.info("Production interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Production error: {e}")
        return False
    finally:
        runner.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)