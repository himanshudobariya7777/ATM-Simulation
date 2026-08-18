"""
Unit tests for fund transfer operations and transaction history auditing.
"""

import pytest
import os
import tempfile
from database.db_manager import DatabaseManager
from services.transaction_service import TransactionService
from services.atm_service import ATMService

@pytest.fixture
def setup_services():
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    db_mgr = DatabaseManager(db_path=db_file.name)
    txn_svc = TransactionService(db_mgr)
    atm_svc = ATMService(db_mgr, txn_svc)
    yield atm_svc, txn_svc, db_mgr
    os.unlink(db_file.name)

def test_transfer_success(setup_services):
    atm_svc, txn_svc, _ = setup_services

    # Initial balance: 1001 (2,000,000), 1002 (2,000,000)
    success, sender_bal, msg = atm_svc.transfer("1001", "1002", 5000.0)
    assert success is True
    assert sender_bal == 1995000.0

    # Recipient balance check
    recipient_acc = atm_svc.get_account("1002")
    assert recipient_acc.balance == 2005000.0

    # Transaction history log verification
    sender_history = txn_svc.get_account_history("1001")
    assert any(t.txn_type == "TRANSFER_OUT" and t.amount == 5000.0 for t in sender_history)

    recipient_history = txn_svc.get_account_history("1002")
    assert any(t.txn_type == "TRANSFER_IN" and t.amount == 5000.0 for t in recipient_history)

def test_transfer_to_invalid_recipient(setup_services):
    atm_svc, _, _ = setup_services
    success, _, msg = atm_svc.transfer("1001", "9999", 1000.0)
    assert success is False
    assert "does not exist" in msg

def test_transfer_self(setup_services):
    atm_svc, _, _ = setup_services
    success, _, msg = atm_svc.transfer("1001", "1001", 1000.0)
    assert success is False
    assert "own account" in msg
