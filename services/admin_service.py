"""
Admin service providing management functions: viewing accounts, account creation/deletion/locking, transaction audit, aggregate reserve calculation, and report generation (TXT/CSV).
"""

import csv
from typing import List, Optional, Tuple
from datetime import datetime
from database.db_manager import DatabaseManager
from models.account import Account
from services.transaction_service import TransactionService
from utils.security import hash_secret
from utils.helpers import get_current_timestamp, format_currency
from utils.logger import logger
from utils.validators import validate_account_number, validate_pin, validate_name
from config import DAILY_REPORT_PATH, TRANSACTION_REPORT_CSV_PATH

class AdminService:
    """Manages administrative operations and system reports."""

    def __init__(self, db_manager: DatabaseManager, transaction_service: TransactionService):
        self.db = db_manager
        self.txn_service = transaction_service

    def get_all_accounts(self) -> List[Account]:
        """Retrieves list of all customer accounts."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY account_id ASC;")
            rows = cursor.fetchall()
            return [
                Account(
                    account_id=r["account_id"],
                    name=r["name"],
                    pin_hash=r["pin_hash"],
                    salt=r["salt"],
                    balance=r["balance"],
                    status=r["status"],
                    failed_attempts=r["failed_attempts"],
                    created_at=r["created_at"]
                ) for r in rows
            ]

    def search_account(self, account_id: str) -> Optional[Account]:
        """Searches account by account_id."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE account_id = ?;", (account_id,))
            r = cursor.fetchone()
            if r:
                return Account(
                    account_id=r["account_id"],
                    name=r["name"],
                    pin_hash=r["pin_hash"],
                    salt=r["salt"],
                    balance=r["balance"],
                    status=r["status"],
                    failed_attempts=r["failed_attempts"],
                    created_at=r["created_at"]
                )
            return None

    def create_account(self, account_id: str, name: str, pin: str, initial_deposit: float = 0.0) -> Tuple[bool, str]:
        """Creates a new customer account."""
        val_acc, err_acc = validate_account_number(account_id)
        if not val_acc:
            return False, err_acc

        val_name, err_name = validate_name(name)
        if not val_name:
            return False, err_name

        val_pin, err_pin = validate_pin(pin)
        if not val_pin:
            return False, err_pin

        if initial_deposit < 0:
            return False, "Initial deposit cannot be negative."

        if self.search_account(account_id):
            return False, f"Account ID '{account_id}' already exists."

        pin_hash, salt = hash_secret(pin)
        created_at = get_current_timestamp()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO accounts (account_id, name, pin_hash, salt, balance, status, failed_attempts, created_at)
                VALUES (?, ?, ?, ?, ?, 'active', 0, ?);
            """, (account_id, name, pin_hash, salt, initial_deposit, created_at))

            if initial_deposit > 0:
                self.txn_service.record_transaction(conn, account_id, "DEPOSIT", initial_deposit, initial_deposit)

        logger.info(f"Admin created new account {account_id} for {name} with balance {initial_deposit}")
        return True, f"Account '{account_id}' for {name} created successfully."

    def delete_account(self, account_id: str) -> Tuple[bool, str]:
        """Deletes a customer account."""
        if not self.search_account(account_id):
            return False, f"Account '{account_id}' does not exist."

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts WHERE account_id = ?;", (account_id,))

        logger.info(f"Admin deleted account {account_id}")
        return True, f"Account '{account_id}' deleted successfully."

    def block_account(self, account_id: str) -> Tuple[bool, str]:
        """Blocks an active account."""
        acc = self.search_account(account_id)
        if not acc:
            return False, f"Account '{account_id}' does not exist."
        if acc.status == "blocked":
            return False, f"Account '{account_id}' is already blocked."

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET status = 'blocked' WHERE account_id = ?;", (account_id,))

        logger.info(f"Admin blocked account {account_id}")
        return True, f"Account '{account_id}' blocked successfully."

    def unblock_account(self, account_id: str) -> Tuple[bool, str]:
        """Unblocks a locked/blocked account and resets failed login attempts."""
        acc = self.search_account(account_id)
        if not acc:
            return False, f"Account '{account_id}' does not exist."
        if acc.status == "active" and acc.failed_attempts == 0:
            return False, f"Account '{account_id}' is already active with 0 failed attempts."

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET status = 'active', failed_attempts = 0 WHERE account_id = ?;", (account_id,))

        logger.info(f"Admin reset failed attempts/unblocked account {account_id}")
        return True, f"Account '{account_id}' activated and failed attempts reset to 0."

    def get_total_bank_reserve(self) -> float:
        """Calculates total deposits reserve across all accounts."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(balance), 0.0) FROM accounts;")
            return float(cursor.fetchone()[0])

    def generate_reports(self) -> Tuple[str, str]:
        """
        Generates:
        1. daily_report.txt summary report.
        2. transaction_report.csv transaction history dump.
        Returns paths of generated files.
        """
        accounts = self.get_all_accounts()
        transactions = self.txn_service.get_all_transactions()
        total_reserve = self.get_total_bank_reserve()

        active_count = sum(1 for a in accounts if a.status == "active")
        blocked_count = sum(1 for a in accounts if a.status in ("blocked", "locked"))

        total_deposits = sum(t.amount for t in transactions if t.txn_type == "DEPOSIT")
        total_withdrawals = sum(t.amount for t in transactions if t.txn_type == "WITHDRAW")
        total_transfers = sum(t.amount for t in transactions if t.txn_type == "TRANSFER_OUT")

        report_timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        # 1. Write daily_report.txt
        daily_text = f"""==============================================
            ATM DAILY SYSTEM REPORT
==============================================
Generated On        : {report_timestamp}

ACCOUNT SUMMARY
----------------------------------------------
Total Accounts      : {len(accounts)}
Active Accounts     : {active_count}
Blocked/Locked      : {blocked_count}

FINANCIAL OVERVIEW
----------------------------------------------
Total Bank Reserve  : {format_currency(total_reserve)}
Total Deposits      : {format_currency(total_deposits)}
Total Withdrawals   : {format_currency(total_withdrawals)}
Total Transfers     : {format_currency(total_transfers)}

TRANSACTION AUDIT
----------------------------------------------
Total Transactions  : {len(transactions)}
==============================================
"""
        with open(DAILY_REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(daily_text)

        # 2. Write transaction_report.csv
        with open(TRANSACTION_REPORT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Transaction ID", "Account ID", "Type", "Amount (INR)", "Balance After (INR)", "Timestamp"])
            for t in transactions:
                writer.writerow([t.transaction_id, t.account_id, t.txn_type, t.amount, t.balance_after, t.timestamp])

        logger.info("Admin generated daily report and exported transactions CSV.")
        return str(DAILY_REPORT_PATH), str(TRANSACTION_REPORT_CSV_PATH)
