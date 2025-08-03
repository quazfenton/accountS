import sys
import time
import random
import argparse
import concurrent.futures
import threading
from pathlib import Path

# Add the current directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent))

from modules.email_registration import EmailRegistration
from modules.social_media_registration import SocialMediaRegistration
from modules.database import Database
from modules.profile_manager import ProfileManager
from utils.notifier import Notifier
from utils.identity_generator import IdentityGenerator # Import IdentityGenerator

# Thread-local storage for account creation components
thread_local = threading.local()

def get_components():
    """Initialize components per thread"""
    if not hasattr(thread_local, "email_reg"):
        from config.config import Config
        config = Config()
        thread_local.email_reg = EmailRegistration(
            headless=config.HEADLESS_MODE,
            debug=config.DEBUG_MODE
        )
        thread_local.db = Database()
        thread_local.profile_manager = ProfileManager()
        thread_local.notifier = Notifier()
    return (
        thread_local.email_reg,
        thread_local.db,
        thread_local.profile_manager,
        thread_local.notifier
    )

def create_account(account_num, total_accounts, platforms):
    """Create a single account with thread-safe components"""
    email_reg, db, profile_manager, notifier = get_components()
    
    try:
        print(f"\n=== Creating account {account_num}/{total_accounts} ===")
        print(f"[{account_num}] Generating identity...")
        
        # Generate detailed identity profile
        profile = profile_manager.generate_full_profile()
        identity = profile['basic']
        
        # Step 1: Register email with identity
        print(f"[{account_num}] Registering email...")
        email_data = email_reg.register_email()
        if not email_data:
            print(f"❌ [{account_num}] Email registration failed. Skipping...")
            return False
        else:
            if email_data.get('status') == 'needs_verification':
                print(f"⚠️ [{account_num}] Email requires verification: {email_data['email']}")
            else:
                print(f"✅ [{account_num}] Email registered: {email_data['email']}")
        
        # Step 2: Register social media accounts with full profile
        social_reg = SocialMediaRegistration(
            email=email_data['email'],
            password=email_data['password'],
            proxy=email_data['proxy']
        )
        social_data = social_reg.register_multiple_platforms(
            platforms,
            identity=profile['basic'], # Pass basic identity
            profile=profile # Pass full profile
        )
        
        # Step 3: Save to database
        if db.save_account(email_data, social_data):
            print(f"💾 [{account_num}] Account saved to database")
        else:
            print(f"❌ [{account_num}] Failed to save account to database")
        
        return True
    
    except Exception as e:
        print(f"⚠️ [{account_num}] Account creation error: {str(e)}")
        notifier.human_intervention_required(
            f"Account {account_num}",
            f"Error: {str(e)}"
        )
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
