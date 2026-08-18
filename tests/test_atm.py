"""
Unit tests for ATM core banking operations (deposit, withdrawal limits, daily cumulative limit, PIN change).
"""

import pytest
import os
import tempfile
from database.db_manager import DatabaseManager
from services.transaction_service import TransactionService
from services.atm_service import ATMService
from config import MIN_WITHDRAWAL_AMOUNT, MAX_SINGLE_WITHDRAWAL_AMOUNT, MAX_DAILY_WITHDRAWAL_LIMIT

@pytest.fixture
def temp_atm():
    """Fixture providing an ATMService instance backed by a temporary database."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    db_mgr = DatabaseManager(db_path=db_file.name)
    txn_svc = TransactionService(db_mgr)
    atm_svc = ATMService(db_mgr, txn_svc)
    yield atm_svc, db_mgr
    os.unlink(db_file.name)

def test_deposit(temp_atm):
    atm_svc, _ = temp_atm
    success, new_bal, msg = atm_svc.deposit("1001", 5000.0)
    assert success is True
    assert new_bal == 2005000.0

def test_withdraw_minimum_limit(temp_atm):
    atm_svc, _ = temp_atm
    success, _, msg = atm_svc.withdraw("1001", 5000.0)
    assert success is False
    assert "Minimum withdrawal amount" in msg

def test_withdraw_maximum_single_limit(temp_atm):
    atm_svc, _ = temp_atm
    success, _, msg = atm_svc.withdraw("1001", 150000.0)
    assert success is False
    assert "Maximum withdrawal limit per transaction" in msg

def test_withdraw_daily_cumulative_limit(temp_atm):
    atm_svc, _ = temp_atm

    # Withdraw 100,000 5 times = 500,000
    for _ in range(5):
        s, _, _ = atm_svc.withdraw("1001", 100000.0)
        assert s is True

    # 6th withdrawal of 10,000 would total 510,000 -> exceeds 500,000 daily limit!
    s_exceed, _, msg = atm_svc.withdraw("1001", 10000.0)
    assert s_exceed is False
    assert "Daily withdrawal limit" in msg

def test_withdraw_insufficient_balance(temp_atm):
    atm_svc, db_mgr = temp_atm
    # Set account 1003 balance to 5000
    with db_mgr.get_connection() as conn:
        conn.cursor().execute("UPDATE accounts SET balance = 5000.0 WHERE account_id = '1003';")
    success, _, msg = atm_svc.withdraw("1003", 10000.0)
    assert success is False
    assert "Insufficient balance" in msg

def test_change_pin(temp_atm):
    atm_svc, _ = temp_atm
    success, msg = atm_svc.change_pin("1001", "12345678", "87654321")
    assert success is True

    # Change pin back or check wrong old pin
    fail, fail_msg = atm_svc.change_pin("1001", "12345678", "00000000")
    assert fail is False
    assert "Incorrect old PIN" in fail_msg
