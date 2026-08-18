"""
ATM Service executing core banking operations: balance inquiry, cash deposit, cash withdrawal, fund transfer, and PIN updates.
"""

from typing import Tuple, Optional
from database.db_manager import DatabaseManager
from models.account import Account
from services.transaction_service import TransactionService
from utils.security import verify_secret, hash_secret
from utils.logger import logger
from config import (
    MIN_WITHDRAWAL_AMOUNT, MAX_SINGLE_WITHDRAWAL_AMOUNT, MAX_DAILY_WITHDRAWAL_LIMIT, CURRENCY_SYMBOL
)

class ATMService:
    """Handles financial transactions for logged-in ATM users."""

    def __init__(self, db_manager: DatabaseManager, transaction_service: TransactionService):
        self.db = db_manager
        self.txn_service = transaction_service

    def get_account(self, account_id: str) -> Optional[Account]:
        """Fetches fresh account details from DB."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE account_id = ?;", (account_id,))
            row = cursor.fetchone()
            if row:
                return Account(
                    account_id=row["account_id"],
                    name=row["name"],
                    pin_hash=row["pin_hash"],
                    salt=row["salt"],
                    balance=row["balance"],
                    status=row["status"],
                    failed_attempts=row["failed_attempts"],
                    created_at=row["created_at"]
                )
            return None

    def get_balance(self, account_id: str) -> Tuple[bool, float, str]:
        """Returns account balance."""
        account = self.get_account(account_id)
        if not account:
            return False, 0.0, "Account not found."
        return True, account.balance, f"Available Balance: {CURRENCY_SYMBOL}{account.balance:,.2f}"

    def deposit(self, account_id: str, amount: float) -> Tuple[bool, float, str]:
        """Deposits funds into the specified account."""
        if amount <= 0:
            return False, 0.0, "Deposit amount must be greater than zero."

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM accounts WHERE account_id = ?;", (account_id,))
            row = cursor.fetchone()
            if not row:
                return False, 0.0, "Account not found."

            current_balance = row["balance"]
            new_balance = round(current_balance + amount, 2)

            cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?;", (new_balance, account_id))
            self.txn_service.record_transaction(conn, account_id, "DEPOSIT", amount, new_balance)

        logger.info(f"Account {account_id} deposited {amount}. New balance: {new_balance}")
        return True, new_balance, f"Deposit of {CURRENCY_SYMBOL}{amount:,.2f} successful. New balance: {CURRENCY_SYMBOL}{new_balance:,.2f}"

    def withdraw(self, account_id: str, amount: float) -> Tuple[bool, float, str]:
        """
        Withdraws cash enforcing withdrawal rules:
        - Min withdrawal = ₹100
        - Max per transaction = ₹20,000
        - Daily cumulative limit = ₹50,000
        - Sufficient balance requirement
        """
        if amount < MIN_WITHDRAWAL_AMOUNT:
            return False, 0.0, f"Minimum withdrawal amount is {CURRENCY_SYMBOL}{MIN_WITHDRAWAL_AMOUNT:,.2f}."

        if amount > MAX_SINGLE_WITHDRAWAL_AMOUNT:
            return False, 0.0, f"Maximum withdrawal limit per transaction is {CURRENCY_SYMBOL}{MAX_SINGLE_WITHDRAWAL_AMOUNT:,.2f}."

        daily_withdrawn = self.txn_service.get_daily_withdrawal_total(account_id)
        if (daily_withdrawn + amount) > MAX_DAILY_WITHDRAWAL_LIMIT:
            remaining_limit = max(0.0, MAX_DAILY_WITHDRAWAL_LIMIT - daily_withdrawn)
            return False, 0.0, (
                f"Daily withdrawal limit of {CURRENCY_SYMBOL}{MAX_DAILY_WITHDRAWAL_LIMIT:,.2f} exceeded! "
                f"You have already withdrawn {CURRENCY_SYMBOL}{daily_withdrawn:,.2f} today. "
                f"Remaining daily limit: {CURRENCY_SYMBOL}{remaining_limit:,.2f}."
            )

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM accounts WHERE account_id = ?;", (account_id,))
            row = cursor.fetchone()
            if not row:
                return False, 0.0, "Account not found."

            current_balance = row["balance"]
            if current_balance < amount:
                return False, current_balance, f"Insufficient balance! Your current balance is {CURRENCY_SYMBOL}{current_balance:,.2f}."

            new_balance = round(current_balance - amount, 2)
            cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?;", (new_balance, account_id))
            self.txn_service.record_transaction(conn, account_id, "WITHDRAW", amount, new_balance)

        logger.info(f"Account {account_id} withdrew {amount}. New balance: {new_balance}")
        return True, new_balance, f"Please collect your cash: {CURRENCY_SYMBOL}{amount:,.2f}. Remaining balance: {CURRENCY_SYMBOL}{new_balance:,.2f}"

    def transfer(self, from_account_id: str, to_account_id: str, amount: float) -> Tuple[bool, float, str]:
        """Performs atomic fund transfer between two customer accounts."""
        if from_account_id == to_account_id:
            return False, 0.0, "Cannot transfer money to your own account."

        if amount <= 0:
            return False, 0.0, "Transfer amount must be greater than zero."

        target_acc = self.get_account(to_account_id)
        if not target_acc:
            return False, 0.0, f"Recipient account '{to_account_id}' does not exist."

        if not target_acc.is_active():
            return False, 0.0, f"Recipient account '{to_account_id}' is inactive or locked."

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Verify sender balance
            cursor.execute("SELECT balance FROM accounts WHERE account_id = ?;", (from_account_id,))
            sender_row = cursor.fetchone()
            if not sender_row:
                return False, 0.0, "Sender account not found."

            sender_bal = sender_row["balance"]
            if sender_bal < amount:
                return False, sender_bal, f"Insufficient balance for transfer! Current balance: {CURRENCY_SYMBOL}{sender_bal:,.2f}."

            # Update sender balance
            new_sender_bal = round(sender_bal - amount, 2)
            cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?;", (new_sender_bal, from_account_id))
            self.txn_service.record_transaction(conn, from_account_id, "TRANSFER_OUT", amount, new_sender_bal)

            # Update recipient balance
            cursor.execute("SELECT balance FROM accounts WHERE account_id = ?;", (to_account_id,))
            recipient_bal = cursor.fetchone()["balance"]
            new_recipient_bal = round(recipient_bal + amount, 2)
            cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?;", (new_recipient_bal, to_account_id))
            self.txn_service.record_transaction(conn, to_account_id, "TRANSFER_IN", amount, new_recipient_bal)

        logger.info(f"Transfer successful: {from_account_id} -> {to_account_id} amount {amount}")
        return True, new_sender_bal, f"Successfully transferred {CURRENCY_SYMBOL}{amount:,.2f} to {target_acc.name} ({to_account_id}). New balance: {CURRENCY_SYMBOL}{new_sender_bal:,.2f}"

    def change_pin(self, account_id: str, old_pin: str, new_pin: str) -> Tuple[bool, str]:
        """Changes PIN for customer account after old PIN verification."""
        account = self.get_account(account_id)
        if not account:
            return False, "Account not found."

        if not verify_secret(old_pin, account.pin_hash, account.salt):
            return False, "Incorrect old PIN."

        if old_pin == new_pin:
            return False, "New PIN cannot be the same as the old PIN."

        new_hash, new_salt = hash_secret(new_pin)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE accounts
                SET pin_hash = ?, salt = ?
                WHERE account_id = ?;
            """, (new_hash, new_salt, account_id))

        logger.info(f"PIN changed successfully for account {account_id}")
        return True, "PIN changed successfully! Please use your new PIN for future logins."
