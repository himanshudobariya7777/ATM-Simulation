"""
Unit tests for authentication service (Customer & Admin PIN verification & account lockouts).
"""

import pytest
import os
import tempfile
from database.db_manager import DatabaseManager
from services.auth_service import AuthService
from services.transaction_service import TransactionService
from services.admin_service import AdminService

@pytest.fixture
def temp_db():
    """Fixture to create a fresh temporary SQLite DB for testing."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_file.close()
    db_manager = DatabaseManager(db_path=db_file.name)
    yield db_manager
    os.unlink(db_file.name)

def test_customer_authentication_success(temp_db):
    auth_service = AuthService(temp_db)
    success, account, msg = auth_service.authenticate_customer("1001", "12345678")
    assert success is True
    assert account is not None
    assert account.account_id == "1001"
    assert account.name == "Himanshu"

def test_customer_authentication_wrong_pin(temp_db):
    auth_service = AuthService(temp_db)
    success, account, msg = auth_service.authenticate_customer("1001", "99999999")
    assert success is False
    assert account is None
    assert "2 attempt(s) remaining" in msg

def test_account_lockout_after_three_failed_attempts(temp_db):
    auth_service = AuthService(temp_db)
    # Attempt 1
    auth_service.authenticate_customer("1001", "00000000")
    # Attempt 2
    auth_service.authenticate_customer("1001", "00000000")
    # Attempt 3 -> Lockout
    success, account, msg = auth_service.authenticate_customer("1001", "00000000")
    assert success is False
    assert "Account locked" in msg

    # Next attempt confirms account is locked
    success, account, msg = auth_service.authenticate_customer("1001", "12345678")
    assert success is False
    assert "LOCKED" in msg

def test_admin_authentication(temp_db):
    auth_service = AuthService(temp_db)
    success, admin, msg = auth_service.authenticate_admin("admin", "admin123")
    assert success is True
    assert admin.username == "admin"

    success_fail, _, _ = auth_service.authenticate_admin("admin", "wrongpass")
    assert success_fail is False

def test_admin_create_account_zero_deposit(temp_db):
    txn_svc = TransactionService(temp_db)
    admin_svc = AdminService(temp_db, txn_svc)
    success, msg = admin_svc.create_account("2001", "New User", "12345678", 0.0)
    assert success is True
    assert "created successfully" in msg
    acc = admin_svc.search_account("2001")
    assert acc is not None
    assert acc.balance == 0.0

def test_admin_create_account_with_initial_deposit(temp_db):
    txn_svc = TransactionService(temp_db)
    admin_svc = AdminService(temp_db, txn_svc)
    success, msg = admin_svc.create_account("2002", "Funded User", "87654321", 2500.0)
    assert success is True
    acc = admin_svc.search_account("2002")
    assert acc is not None
    assert acc.balance == 2500.0

def test_admin_create_account_duplicate_id(temp_db):
    txn_svc = TransactionService(temp_db)
    admin_svc = AdminService(temp_db, txn_svc)
    success, msg = admin_svc.create_account("1001", "Duplicate User", "12345678", 0.0)
    assert success is False
    assert "already exists" in msg
