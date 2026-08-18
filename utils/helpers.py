"""
Helper functions for formatting currency, timestamps, and transaction IDs.
"""

from datetime import datetime
from config import CURRENCY_SYMBOL

def format_currency(amount: float) -> str:
    """Formats a float amount into currency format (e.g., ₹1,00,000.00)."""
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"


def get_current_timestamp() -> str:
    """Returns ISO format timestamp for database storage."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_transaction_id() -> str:
    """Generates a unique transaction ID format: TXNyyyyMMddHHmmssXXXX"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d%H%M%S")
    micro_str = f"{now.microsecond:06d}"[:4]
    return f"TXN{date_str}{micro_str}"
