"""
Account domain model representing a customer bank account.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Account:
    account_id: str
    name: str
    pin_hash: str
    salt: str
    balance: float
    status: str = "active"  # "active", "locked", "blocked"
    failed_attempts: int = 0
    created_at: str = ""

    def is_active(self) -> bool:
        return self.status.lower() == "active"

    def is_locked(self) -> bool:
        return self.status.lower() in ("locked", "blocked")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "name": self.name,
            "balance": self.balance,
            "status": self.status,
            "failed_attempts": self.failed_attempts,
            "created_at": self.created_at
        }
