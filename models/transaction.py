"""
Transaction domain model representing a financial transaction log entry.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Transaction:
    transaction_id: str
    account_id: str
    txn_type: str  # "DEPOSIT", "WITHDRAW", "TRANSFER_OUT", "TRANSFER_IN"
    amount: float
    balance_after: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "type": self.txn_type,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "timestamp": self.timestamp
        }
