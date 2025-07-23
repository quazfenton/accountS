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
            self.client.table(self.table_name).create(if_not_exists=True).execute()
        except Exception as e:
            print(f"Error creating table: {str(e)}")
    
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