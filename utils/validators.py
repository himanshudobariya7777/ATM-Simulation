"""
Input validation utilities for account numbers, PINs, names, and transaction amounts.
"""

from typing import Tuple, Optional
from config import PIN_LENGTH

def validate_account_number(account_id: str) -> Tuple[bool, str]:
    """Validates that account ID is non-empty, numeric, and exactly 4 digits."""
    acc = account_id.strip()
    if not acc:
        return False, "Account number cannot be empty."
    if not acc.isdigit():
        return False, "Account number must contain digits only."
    if len(acc) != 4:
        return False, "Account number must be exactly 4 digits."
    return True, ""


def validate_pin(pin: str) -> Tuple[bool, str]:
    """Validates that PIN is exactly PIN_LENGTH numeric digits."""
    p = pin.strip()
    if not p:
        return False, "PIN cannot be empty."
    if not p.isdigit():
        return False, "PIN must contain numeric digits only."
    if len(p) != PIN_LENGTH:
        return False, f"PIN must be exactly {PIN_LENGTH} digits."
    return True, ""


def validate_amount(amount_str: str) -> Tuple[bool, Optional[float], str]:
    """Validates that amount is a positive number with at most 2 decimal places."""
    try:
        amount = float(amount_str.strip())
        if amount <= 0:
            return False, None, "Amount must be greater than zero."
        if round(amount, 2) != amount:
            return False, None, "Amount cannot have more than 2 decimal places."
        return True, amount, ""
    except ValueError:
        return False, None, "Invalid amount. Please enter a valid number."


def validate_name(name: str) -> Tuple[bool, str]:
    """Validates account holder name."""
    n = name.strip()
    if not n:
        return False, "Name cannot be empty."
    if len(n) < 2:
        return False, "Name must be at least 2 characters long."
    if not all(c.isalpha() or c.isspace() for c in n):
        return False, "Name can only contain alphabetic characters and spaces."
    return True, ""
