"""
Authentication service managing customer login, PIN verification, account lockout, and admin authentication.
"""

from typing import Tuple, Optional
from database.db_manager import DatabaseManager
from models.account import Account
from models.admin import Admin
from utils.security import verify_secret
from utils.logger import logger
from config import MAX_LOGIN_ATTEMPTS

class AuthService:
    """Handles customer and admin authentication logic."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def authenticate_customer(self, account_id: str, pin: str) -> Tuple[bool, Optional[Account], str]:
        """
        Authenticates a customer account by account ID and PIN.
        Increments failed attempt count on wrong PIN and locks account after 3 failures.
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE account_id = ?;", (account_id,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Failed login attempt for non-existent account: {account_id}")
                return False, None, "Account not found."

            account = Account(
                account_id=row["account_id"],
                name=row["name"],
                pin_hash=row["pin_hash"],
                salt=row["salt"],
                balance=row["balance"],
                status=row["status"],
                failed_attempts=row["failed_attempts"],
                created_at=row["created_at"]
            )

            # Check if account is locked/blocked
            if account.is_locked():
                logger.warning(f"Login attempt on locked/blocked account: {account_id}")
                return False, None, f"Account '{account_id}' is {account.status.upper()}. Please contact bank admin."

            # Verify PIN
            if verify_secret(pin, account.pin_hash, account.salt):
                # Reset failed attempts on success
                cursor.execute("""
                    UPDATE accounts
                    SET failed_attempts = 0
                    WHERE account_id = ?;
                """, (account_id,))
                account.failed_attempts = 0
                logger.info(f"Successful login for account: {account_id} ({account.name})")
                return True, account, "Login successful."

            # Invalid PIN logic
            new_attempts = account.failed_attempts + 1
            if new_attempts >= MAX_LOGIN_ATTEMPTS:
                cursor.execute("""
                    UPDATE accounts
                    SET failed_attempts = ?, status = 'locked'
                    WHERE account_id = ?;
                """, (new_attempts, account_id))
                logger.warning(f"Account {account_id} LOCKED due to {new_attempts} consecutive failed PIN attempts.")
                return False, None, f"Incorrect PIN! Account locked after {MAX_LOGIN_ATTEMPTS} failed attempts."
            else:
                cursor.execute("""
                    UPDATE accounts
                    SET failed_attempts = ?
                    WHERE account_id = ?;
                """, (new_attempts, account_id))
                attempts_left = MAX_LOGIN_ATTEMPTS - new_attempts
                logger.warning(f"Failed PIN attempt {new_attempts} for account {account_id}.")
                return False, None, f"Incorrect PIN! {attempts_left} attempt(s) remaining before account lockout."

    def authenticate_admin(self, username: str, password: str) -> Tuple[bool, Optional[Admin], str]:
        """Authenticates an admin user by username and password."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE username = ?;", (username,))
            row = cursor.fetchone()

            if not row:
                return False, None, "Invalid admin username or password."

            admin = Admin(
                admin_id=row["admin_id"],
                username=row["username"],
                password_hash=row["password_hash"],
                salt=row["salt"],
                created_at=row["created_at"]
            )

            if verify_secret(password, admin.password_hash, admin.salt):
                logger.info(f"Admin '{username}' logged in successfully.")
                return True, admin, "Admin login successful."
            else:
                logger.warning(f"Failed admin login attempt for username: {username}")
                return False, None, "Invalid admin username or password."
