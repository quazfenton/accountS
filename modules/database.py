from supabase import create_client
from config.config import Config
import json

class Database:
    def __init__(self):
        self.config = Config()
        self.client = create_client(self.config.SUPABASE_URL, self.config.SUPABASE_KEY)
        self.table_name = "bot_accounts"
    
    def create_table(self):
        """Create accounts table if not exists"""
        try:
            # Check if table exists first
            try:
                self.client.table(self.table_name).select("*").limit(1).execute()
                print(f"Table '{self.table_name}' already exists")
                return True
            except Exception:
                # Table doesn't exist, create it
                pass
            
            # Create table using SQL
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                email_password VARCHAR(255) NOT NULL,
                proxy VARCHAR(255),
                social_credentials JSONB,
                full_profile JSONB,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """
            
            # Execute the SQL
            result = self.client.rpc('exec_sql', {'sql': create_table_sql}).execute()
            print(f"Table '{self.table_name}' created successfully")
            return True
            
        except Exception as e:
            print(f"Error creating table: {str(e)}")
            # Try alternative approach - just attempt to insert and let it fail gracefully
            return True  # Return True to continue execution
    
    def save_account(self, email_data, social_data, profile=None):
        """Save account credentials and full profile to database"""
        try:
            account_data = {
                "email": email_data["email"],
                "email_password": email_data["password"],
                "proxy": email_data["proxy"],
                "social_credentials": json.dumps(social_data),
                "status": "active"
            }
            
            # Add profile data if available
            if profile:
                account_data["full_profile"] = json.dumps(profile)
            
            response = self.client.table(self.table_name).insert(account_data).execute()
            if response.data:
                return True
        except Exception as e:
            print(f"Error saving account: {str(e)}")
        return False
    
    def get_accounts(self, platform=None, status="active"):
        """Retrieve accounts from database"""
        try:
            query = self.client.table(self.table_name).select("*").eq("status", status)
            if platform:
                query = query.like("social_credentials", f'%{platform}%')
                
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error retrieving accounts: {str(e)}")
        return []
    
    def update_account_status(self, email, status):
        """Update account status"""
        try:
            self.client.table(self.table_name).update({"status": status}).eq("email", email).execute()
            return True
        except Exception as e:
            print(f"Error updating account status: {str(e)}")
        return False
    
    def save_account_ecosystem(self, ecosystem_data):
        """Save account ecosystem data to database"""
        try:
            # Extract primary account data
            primary_account = ecosystem_data.get('primary_account', {})
            linked_accounts = ecosystem_data.get('linked_accounts', [])
            
            # Prepare main account data
            account_data = {
                "email": primary_account.get('email', ''),
                "email_password": primary_account.get('password', ''),
                "proxy": '',  # Will be managed by proxy manager
                "social_credentials": json.dumps({
                    'linked_accounts': linked_accounts,
                    'ecosystem_metadata': {
                        'identity_seed': ecosystem_data.get('identity_seed', ''),
                        'creation_strategy': ecosystem_data.get('creation_strategy', ''),
                        'success_rate': ecosystem_data.get('success_rate', 0),
                        'total_creation_time': ecosystem_data.get('total_creation_time', 0)
                    }
                }),
                "full_profile": json.dumps(primary_account.get('profile_data', {})),
                "status": "active"
            }
            
            # Insert into database
            response = self.client.table(self.table_name).insert(account_data).execute()
            
            if response.data:
                print(f"Account ecosystem saved with ID: {response.data[0]['id']}")
                return True
            else:
                print("Failed to save account ecosystem - no data returned")
                return False
                
        except Exception as e:
            print(f"Database ecosystem save error: {str(e)}")
            return False