"""
Transaction service for logging financial operations and retrieving transaction history/reports.
"""

from typing import List
from datetime import datetime
from database.db_manager import DatabaseManager
from models.transaction import Transaction
from utils.helpers import generate_transaction_id, get_current_timestamp
from utils.logger import logger

class TransactionService:
    """Manages transaction history recording and querying."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def record_transaction(self, conn, account_id: str, txn_type: str, amount: float, balance_after: float) -> str:
        """
        Records a new transaction using an existing active DB connection/transaction.
        Returns the generated transaction ID.
        """
        txn_id = generate_transaction_id()
        timestamp = get_current_timestamp()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (transaction_id, account_id, type, amount, balance_after, timestamp)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (txn_id, account_id, txn_type, amount, balance_after, timestamp))
        logger.info(f"Recorded transaction {txn_id}: {txn_type} {amount} on account {account_id}")
        return txn_id

    def get_account_history(self, account_id: str, limit: int = 20) -> List[Transaction]:
        """Retrieves transaction history for a specific account."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transactions
                WHERE account_id = ?
                ORDER BY timestamp DESC
                LIMIT ?;
            """, (account_id, limit))
            rows = cursor.fetchall()
            return [
                Transaction(
                    transaction_id=r["transaction_id"],
                    account_id=r["account_id"],
                    txn_type=r["type"],
                    amount=r["amount"],
                    balance_after=r["balance_after"],
                    timestamp=r["timestamp"]
                ) for r in rows
            ]

    def get_all_transactions(self) -> List[Transaction]:
        """Retrieves all transactions across all accounts."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC;")
            rows = cursor.fetchall()
            return [
                Transaction(
                    transaction_id=r["transaction_id"],
                    account_id=r["account_id"],
                    txn_type=r["type"],
                    amount=r["amount"],
                    balance_after=r["balance_after"],
                    timestamp=r["timestamp"]
                ) for r in rows
            ]

    def get_daily_withdrawal_total(self, account_id: str) -> float:
        """Calculates total cumulative amount withdrawn by an account on the current day."""
        today_date = datetime.now().strftime("%Y-%m-%d")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0.0) FROM transactions
                WHERE account_id = ?
                  AND type = 'WITHDRAW'
                  AND timestamp LIKE ?;
            """, (account_id, f"{today_date}%"))
            total = cursor.fetchone()[0]
            return float(total)
