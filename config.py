"""
Configuration settings and constants for the ATM Simulation system.
"""

from pathlib import Path

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent

# Database Configuration
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "atm.db"

# Reports Configuration
REPORTS_DIR = BASE_DIR / "reports"
DAILY_REPORT_PATH = REPORTS_DIR / "daily_report.txt"
TRANSACTION_REPORT_CSV_PATH = REPORTS_DIR / "transaction_report.csv"

# Log Configuration
LOG_FILE_PATH = BASE_DIR / "atm_app.log"

# Financial Rules & Limits (in INR ₹)
MIN_WITHDRAWAL_AMOUNT = 10000.0
MAX_SINGLE_WITHDRAWAL_AMOUNT = 100000.0
MAX_DAILY_WITHDRAWAL_LIMIT = 500000.0
CURRENCY_SYMBOL = "₹"

# Security Rules
MAX_LOGIN_ATTEMPTS = 3
PIN_LENGTH = 8

# Seed Admin Credentials
DEFAULT_ADMIN_ID = "ADMIN001"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

# Ensure essential directories exist
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
