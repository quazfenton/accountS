from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class AccountCreationResult:
    success: bool
    account_data: Dict[str, Any]
    error_message: Optional[str] = None
    requires_human_intervention: bool = False

class AbstractAccountManager(ABC):
    """Abstract base class for account managers"""
    
    @abstractmethod
    async def create_single_account(self, identity: Dict[str, Any], platforms: List[str]) -> AccountCreationResult:
        """Create a single account across multiple platforms"""
        pass
    
    @abstractmethod
    async def create_accounts_batch(self, identities: List[Dict[str, Any]], platforms: List[str]) -> Dict[str, Any]:
        """Create multiple accounts in batch"""
        pass
    
    @abstractmethod
    async def verify_account(self, account_data: Dict[str, Any]) -> bool:
        """Verify an existing account"""
        pass
    
    @abstractmethod
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get current session statistics"""
        pass