import sys
import time
import random
import argparse
import asyncio
import concurrent.futures
import threading
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

# Thread-local storage for account creation components
thread_local = threading.local()

def get_components():
    """Initialize components per thread with improved features"""
    if not hasattr(thread_local, "account_manager"):
        # Load advanced configuration
        try:
            config = AdvancedConfig()
            proxy_list = [proxy.url for proxy in config.proxies] if config.should_use_proxy() else None
        except Exception as e:
            print(f"Warning: Could not load advanced config, using basic setup: {e}")
            proxy_list = None
        
        # Initialize improved account manager (main component)
        thread_local.account_manager = ImprovedAccountManager(
            proxy_list=proxy_list,
            max_workers=5,
            db_path="accounts.db"
        )
        
        # Legacy components for backward compatibility
        from config.config import Config
        legacy_config = Config()
        thread_local.email_reg = EmailRegistration(
            headless=legacy_config.HEADLESS_MODE,
            debug=legacy_config.DEBUG_MODE
        )
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

async def create_account_advanced(account_num, total_accounts, platforms):
    """Create account using improved account manager"""
    account_manager, db, notifier, email_reg, profile_manager = get_components()
    
    try:
        print(f"\n=== Creating advanced account ecosystem {account_num}/{total_accounts} ===")
        print(f"[{account_num}] Platforms: {platforms}")
        
        # Generate identity using profile manager
        profile = profile_manager.generate_full_profile()
        identity = profile['basic']
        
        # Create account using improved manager
        result = await account_manager.create_single_account(identity, platforms)
        
        # Print results
        if result['success']:
            print(f"✅ [{account_num}] Account ecosystem created successfully")
            print(f"📧 [{account_num}] Primary email: {result.get('primary_email', 'N/A')}")
            print(f"📊 [{account_num}] Success rate: {result.get('success_rate', 0):.2%}")
            print(f"⏱️ [{account_num}] Duration: {result.get('duration', 0):.1f}s")
            
            # Save to legacy database as well for compatibility
            if 'ecosystem' in result:
                ecosystem_data = result['ecosystem']
                primary_account = ecosystem_data.get('primary_account', {})
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
            print(f"❌ [{account_num}] Account creation failed: {result.get('error', 'Unknown error')}")
            
            # Check if human intervention is needed
            if result.get('requires_human_intervention'):
                notifier.human_intervention_required(
                    f"Account {account_num}",
                    f"Human intervention required: {result.get('error', 'Unknown issue')}"
                )
            
            return False
        
    except Exception as e:
        print(f"⚠️ [{account_num}] Advanced account creation error: {str(e)}")
        notifier.human_intervention_required(
            f"Account {account_num}",
            f"Critical error: {str(e)}"
        )
        return False

def create_account(account_num, total_accounts, platforms):
    """Legacy account creation method (synchronous wrapper)"""
    try:
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(create_account_advanced(account_num, total_accounts, platforms))
        finally:
            loop.close()
    except Exception as e:
        print(f"⚠️ [{account_num}] Error in account creation wrapper: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Bot Account Manager')
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
        print(f"Database initialization failed: {str(e)}")
        Notifier().human_intervention_required("Database", f"Initialization failed: {str(e)}")
        return
    
    if args.traverse_identities:
        print(f"\n=== Demonstrating Identity Traversal (Depth: {args.traversal_depth}, Strength: {args.traversal_strength}) ===")
        profile_manager = ProfileManager()
        identity_gen = IdentityGenerator() # Create an instance of IdentityGenerator
        
        # Generate a base profile for traversal
        base_profile = profile_manager.generate_full_profile(seed=42) # Use a seed for reproducibility
        print(f"Base Profile Username: {base_profile['basic']['username']}")
        
        # Perform identity traversal
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
            print("\nOperation cancelled by user")
            sys.exit(0)
        except Exception as e:
            print(f"Critical error: {str(e)}")
            Notifier().human_intervention_required("Main Process", f"Critical error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
