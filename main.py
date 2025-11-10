import sys
import time
import random
import argparse
import asyncio
import concurrent.futures
import threading
import logging
import logging.config
from pathlib import Path

# Add the current directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent))

from modules.email_registration import EmailRegistration
from modules.social_media_registration import SocialMediaRegistration
from modules.account_orchestrator import AccountOrchestrator
from modules.improved_account_manager import ImprovedAccountManager
from modules.improved_database import ImprovedDatabase
from modules.database import Database
from modules.profile_manager import ProfileManager
from utils.notifier import Notifier
from utils.identity_generator import IdentityGenerator
from utils.proxy_manager import ImprovedProxyManager
from utils.monitoring import MetricsCollector, PerformanceMonitor, AlertManager
from config.advanced_config import AdvancedConfig
from core.service_container import container, DIEnabledAccountManager
from core.config_factory import get_config
from interfaces.verification_service import AbstractVerificationService
from interfaces.proxy_service import AbstractProxyService
from services.concrete_verification_service import ConcreteVerificationService
from services.concrete_proxy_service import ConcreteProxyService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Thread-local storage for account creation components
thread_local = threading.local()

def get_components():
    """Initialize components per thread with improved features and proper error handling"""
    try:
        if not hasattr(thread_local, "account_manager"):
            # Load enhanced configuration
            try:
                config_manager = get_config()
                config = config_manager.get_proxy_config()
                proxy_list = config.get('list', [])
                proxy_enabled = config.get('enabled', False)
            except Exception as e:
                logger.warning(f"Could not load enhanced config, using basic setup: {e}")
                try:
                    basic_config = AdvancedConfig()
                    proxy_list = [proxy.url for proxy in basic_config.proxies] if basic_config.should_use_proxy() else []
                    proxy_enabled = bool(proxy_list)
                except Exception:
                    logger.warning("Could not load any config, using empty proxy list")
                    proxy_list = []
                    proxy_enabled = False
        
            # Initialize DI-enabled account manager (main component)
            try:
                # Set up services with dependency injection
                verification_service = ConcreteVerificationService()
                proxy_service = ConcreteProxyService(proxy_list if proxy_enabled else [])
                
                thread_local.account_manager = DIEnabledAccountManager(
                    verification_service=verification_service,
                    proxy_service=proxy_service,
                    captcha_service=None,  # Will be implemented as needed
                    email_service=None,    # Will be implemented as needed
                    database=ImprovedDatabase(),
                    metrics_collector=MetricsCollector()
                )
            except Exception as e:
                logger.error(f"Failed to initialize DI-enabled account manager: {e}")
                # Fallback to legacy account manager
                thread_local.account_manager = ImprovedAccountManager(
                    proxy_list=proxy_list if proxy_enabled else None,
                    max_workers=5,
                    db_path="accounts.db"
                )
        
            # Legacy components for backward compatibility
            try:
                from config.config import Config
                legacy_config = Config()
                thread_local.email_reg = EmailRegistration(
                    headless=legacy_config.HEADLESS_MODE,
                    debug=legacy_config.DEBUG_MODE
                )
            except Exception as e:
                logger.error(f"Failed to initialize legacy email registration: {e}")
                thread_local.email_reg = None
                
            thread_local.db = Database()
            thread_local.profile_manager = ProfileManager()
            thread_local.notifier = Notifier()
        
        return (
            thread_local.account_manager,
            thread_local.db,
            thread_local.notifier,
            thread_local.email_reg,
            thread_local.profile_manager
        )
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        raise

async def create_account_advanced(account_num, total_accounts, platforms):
    """Create account using improved account manager with comprehensive error handling"""
    try:
        account_manager, db, notifier, email_reg, profile_manager = get_components()
        
        print(f"\n=== Creating advanced account ecosystem {account_num}/{total_accounts} ===")
        print(f"[{account_num}] Platforms: {platforms}")
        
        # Generate identity using profile manager
        profile = profile_manager.generate_full_profile()
        identity = profile['basic']
        
        # Validate identity before proceeding
        if not identity.get('email') or not identity.get('password') or not identity.get('username'):
            raise ValueError(f"Invalid identity generated for account {account_num}: missing required fields")
        
        # Create account using account manager
        if hasattr(account_manager, 'create_single_account'):
            result = await account_manager.create_single_account(identity, platforms)
        else:
            # Fallback to legacy method
            result = await account_manager._create_single_account_ecosystem(
                identity, platforms, f"legacy_{account_num}", 'ecosystem'
            )
        
        # Print results
        if result.success if hasattr(result, 'success') else result.get('success', False):
            success_val = result.success if hasattr(result, 'success') else result.get('success', False)
            primary_email = getattr(result, 'account_data', {}).get('email', result.get('primary_email', 'N/A'))
            
            print(f"✅ [{account_num}] Account ecosystem created successfully")
            print(f"📧 [{account_num}] Primary email: {primary_email}")
            
            # Save to legacy database as well for compatibility
            if hasattr(result, 'account_data') or 'ecosystem' in (result if isinstance(result, dict) else {}):
                ecosystem_data = getattr(result, 'account_data', result.get('ecosystem', {}))
                primary_account = ecosystem_data if isinstance(ecosystem_data, dict) else {}
                if primary_account:
                    legacy_email_data = {
                        'email': primary_account.get('email', ''),
                        'password': primary_account.get('password', ''),
                        'proxy': ''
                    }
                    legacy_social_data = ecosystem_data.get('linked_accounts', [])
                    db.save_account(legacy_email_data, legacy_social_data, profile)
            
            return True
        else:
            error_msg = getattr(result, 'error_message', result.get('error', 'Unknown error'))
            print(f"❌ [{account_num}] Account creation failed: {error_msg}")
            
            # Check if human intervention is needed
            requires_intervention = getattr(result, 'requires_human_intervention', 
                                          result.get('requires_human_intervention', False))
            if requires_intervention:
                notifier.human_intervention_required(
                    f"Account {account_num}",
                    f"Human intervention required: {error_msg}"
                )
            
            return False
        
    except ValueError as ve:
        logger.error(f"Validation error for account {account_num}: {ve}")
        print(f"⚠️ [{account_num}] Validation error: {str(ve)}")
        if 'notifier' in locals():
            notifier.human_intervention_required(
                f"Account {account_num}",
                f"Validation error: {str(ve)}"
            )
        return False
    except Exception as e:
        logger.error(f"Advanced account creation error for account {account_num}: {e}", exc_info=True)
        print(f"⚠️ [{account_num}] Advanced account creation error: {str(e)}")
        try:
            notifier.human_intervention_required(
                f"Account {account_num}",
                f"Critical error: {str(e)}"
            )
        except:
            pass  # Notifier might not be initialized in error case
        return False

def create_account(account_num, total_accounts, platforms):
    """Legacy account creation method (synchronous wrapper) with enhanced error handling"""
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(create_account_advanced(account_num, total_accounts, platforms))
        except Exception as e:
            logger.error(f"Event loop error for account {account_num}: {e}", exc_info=True)
            return False
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Error in account creation wrapper for account {account_num}: {e}", exc_info=True)
        print(f"⚠️ [{account_num}] Error in account creation wrapper: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Bot Account Manager with Enhanced Architecture')
    parser.add_argument('--accounts', type=int, default=1, # Changed default to 1 for quicker testing
                        help='Number of accounts to create')
    parser.add_argument('--threads', type=int, default=1, # Changed default to 1 for simpler testing
                        help='Number of parallel execution threads')
    parser.add_argument('--platforms', nargs='+', default=['twitter'], # Changed default to twitter for simpler testing
                        help='Social media platforms to register')
    parser.add_argument('--traverse-identities', action='store_true',
                        help='Enable identity traversal demonstration')
    parser.add_argument('--traversal-depth', type=int, default=5,
                        help='Depth of identity traversal')
    parser.add_argument('--traversal-strength', type=str, default='medium',
                        choices=['low', 'medium', 'high'],
                        help='Strength of variations during identity traversal')
    args = parser.parse_args()
    
    # Initialize database in main thread
    db = Database()
    try:
        db.create_table()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        print(f"Database initialization failed: {str(e)}")
        try:
            Notifier().human_intervention_required("Database", f"Initialization failed: {str(e)}")
        except:
            pass  # Notifier might not be available
        return
    
    if args.traverse_identities:
        print(f"\n=== Demonstrating Identity Traversal (Depth: {args.traversal_depth}, Strength: {args.traversal_strength}) ===")
        profile_manager = ProfileManager()
        identity_gen = IdentityGenerator() # Create an instance of IdentityGenerator
        
        # Generate a base profile for traversal
        base_profile = profile_manager.generate_full_profile(seed=42) # Use a seed for reproducibility
        print(f"Base Profile Username: {base_profile['basic']['username']}")
        
        # Perform identity traversal
        try:
            identity_graph, traversal_path = identity_gen.traverse_namespace(
                base_profile,
                profile_manager, # Pass profile_manager instance
                depth=args.traversal_depth,
                variation_strength=args.traversal_strength
            )
            
            print("\nIdentity Traversal Path:")
            for i, username in enumerate(traversal_path):
                print(f"  {i+1}. {username}")
                
            print("\nIdentity Graph (Parent -> Children):")
            for parent, children in identity_graph.items():
                print(f"  {parent} -> {', '.join(children)}")
                
            print("\nIdentity traversal demonstration complete.")
        except Exception as e:
            logger.error(f"Identity traversal error: {e}", exc_info=True)
            print(f"Identity traversal error: {e}")
        
    else:
        print(f"Starting account creation for {args.accounts} accounts across {args.threads} threads")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                futures = []
                for i in range(args.accounts):
                    # Add random delay between starting threads
                    delay = random.uniform(0, 5)
                    time.sleep(delay)
                    
                    futures.append(
                        executor.submit(
                            create_account,
                            i+1,
                            args.accounts,
                            args.platforms
                        )
                    )
                
                # Wait for all futures to complete
                results = [f.result() for f in futures]
                success_count = sum(1 for r in results if r)
                print(f"\nAccount creation completed: {success_count}/{args.accounts} successful")
        
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            print("\nOperation cancelled by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Critical error in main execution: {e}", exc_info=True)
            print(f"Critical error: {str(e)}")
            try:
                Notifier().human_intervention_required("Main Process", f"Critical error: {str(e)}")
            except:
                pass  # Notifier might not be available
            sys.exit(1)

if __name__ == "__main__":
    main()
