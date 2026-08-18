"""
SQLite Database Manager handling schema initialization, connection management, and default data seeding.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
from config import (
    DATABASE_PATH, DEFAULT_ADMIN_ID, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD
)
from utils.security import hash_secret
from utils.helpers import get_current_timestamp
from utils.logger import logger


class DatabaseManager:
    """Manages SQLite database connections and table creation."""

    def __init__(self, db_path: str = str(DATABASE_PATH)):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for obtaining a database connection with auto-commit/rollback."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error occurred: {e}")
            raise e
        finally:
            conn.close()

    def init_db(self):
        """Creates tables if they do not exist and seeds initial data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create Accounts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    pin_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'active',
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
            """)

            # Create Transactions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
                );
            """)

            # Create Admins Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    admin_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

        self._seed_initial_data()

    def _seed_initial_data(self):
        """Seeds initial admin user and default test accounts if database is fresh."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Seed Admin
            cursor.execute("SELECT COUNT(*) FROM admins;")
            if cursor.fetchone()[0] == 0:
                pass_hash, salt = hash_secret(DEFAULT_ADMIN_PASSWORD)
                cursor.execute("""
                    INSERT INTO admins (admin_id, username, password_hash, salt, created_at)
                    VALUES (?, ?, ?, ?, ?);
                """, (DEFAULT_ADMIN_ID, DEFAULT_ADMIN_USERNAME, pass_hash, salt, get_current_timestamp()))
                logger.info("Default admin user created.")

            # Seed Customer Accounts
            cursor.execute("SELECT COUNT(*) FROM accounts;")
            if cursor.fetchone()[0] == 0:
                sample_accounts = [
                    ("1001", "Himanshu", "12345678", 2000000.0),
                    ("1002", "Rahul",    "87654321", 2000000.0),
                    ("1003", "Jay",      "11223344", 2000000.0),
                    ("1004", "Priya",    "55667788", 2000000.0),
                    ("1005", "Anish",    "99887766", 2000000.0),
                    ("1006", "Sneha",    "11112222", 2000000.0),
                    ("1007", "Amit",     "33334444", 2000000.0),
                    ("1008", "Pooja",    "55556666", 2000000.0),
                    ("1009", "Rohan",    "77778888", 2000000.0),
                    ("1010", "Kavya",    "99990000", 2000000.0),
                    ("1011", "Vikas",    "12121212", 2000000.0),
                    ("1012", "Neha",     "34343434", 2000000.0),
                    ("1013", "Suresh",   "56565656", 2000000.0),
                    ("1014", "Ritu",     "78787878", 2000000.0),
                    ("1015", "Deepak",   "90909090", 2000000.0),
                    ("1016", "Divya",    "13579246", 2000000.0),
                    ("1017", "Manoj",    "24681357", 2000000.0),
                    ("1018", "Swati",    "98765432", 2000000.0),
                    ("1019", "Alok",     "87651234", 2000000.0),
                    ("1020", "Meera",    "43218765", 2000000.0),
                ]
                now_ts = get_current_timestamp()
                for acc_id, name, pin, balance in sample_accounts:
                    pin_hash, salt = hash_secret(pin)
                    cursor.execute("""
                        INSERT INTO accounts (account_id, name, pin_hash, salt, balance, status, failed_attempts, created_at)
                        VALUES (?, ?, ?, ?, ?, 'active', 0, ?);
                    """, (acc_id, name, pin_hash, salt, balance, now_ts))
                    
                    # Record initial opening balance transaction
                    txn_id = f"TXN{now_ts.replace('-', '').replace(':', '').replace(' ', '')}{acc_id}INIT"
                    cursor.execute("""
                        INSERT INTO transactions (transaction_id, account_id, type, amount, balance_after, timestamp)
                        VALUES (?, ?, 'DEPOSIT', ?, ?, ?);
                    """, (txn_id, acc_id, balance, balance, now_ts))

                logger.info("Initial customer accounts and transaction histories seeded successfully.")
