"""
Flask Web Application & REST API Server for ATM Simulation System.
Serves Web GUI and handles customer/admin API requests.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from database.db_manager import DatabaseManager
from services.auth_service import AuthService
from services.transaction_service import TransactionService
from services.atm_service import ATMService
from services.admin_service import AdminService
from utils.validators import validate_account_number, validate_pin, validate_amount, validate_name
from config import REPORTS_DIR, CURRENCY_SYMBOL

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = 'atm_secret_key_2026_super_secure'

# Initialize Services
db_mgr = DatabaseManager()
txn_service = TransactionService(db_mgr)
auth_service = AuthService(db_mgr)
atm_service = ATMService(db_mgr, txn_service)
admin_service = AdminService(db_mgr, txn_service)


@app.route("/")
def index():
    """Renders the main single-page ATM browser interface."""
    return render_template("index.html")


# =========================================================================
# CUSTOMER API ENDPOINTS
# =========================================================================

@app.route("/api/auth/login/customer", methods=["POST"])
def customer_login():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    pin = str(data.get("pin", "")).strip()

    val_acc, err_acc = validate_account_number(account_id)
    if not val_acc:
        return jsonify({"success": False, "message": err_acc}), 400

    val_pin, err_pin = validate_pin(pin)
    if not val_pin:
        return jsonify({"success": False, "message": err_pin}), 400

    success, account, message = auth_service.authenticate_customer(account_id, pin)
    if success and account:
        return jsonify({
            "success": True,
            "message": message,
            "account": account.to_dict()
        })
    else:
        return jsonify({"success": False, "message": message}), 401


@app.route("/api/customer/account/<account_id>", methods=["GET"])
def get_customer_account(account_id):
    account = atm_service.get_account(account_id)
    if not account:
        return jsonify({"success": False, "message": "Account not found"}), 404
    return jsonify({"success": True, "account": account.to_dict()})


@app.route("/api/customer/deposit", methods=["POST"])
def customer_deposit():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    amount_raw = str(data.get("amount", "")).strip()

    val_amt, amount, err_amt = validate_amount(amount_raw)
    if not val_amt or amount is None:
        return jsonify({"success": False, "message": err_amt}), 400

    success, new_bal, msg = atm_service.deposit(account_id, amount)
    if success:
        return jsonify({"success": True, "new_balance": new_bal, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@app.route("/api/customer/withdraw", methods=["POST"])
def customer_withdraw():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    amount_raw = str(data.get("amount", "")).strip()

    val_amt, amount, err_amt = validate_amount(amount_raw)
    if not val_amt or amount is None:
        return jsonify({"success": False, "message": err_amt}), 400

    success, new_bal, msg = atm_service.withdraw(account_id, amount)
    if success:
        return jsonify({"success": True, "new_balance": new_bal, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@app.route("/api/customer/transfer", methods=["POST"])
def customer_transfer():
    data = request.get_json() or {}
    from_account_id = str(data.get("from_account_id", "")).strip()
    to_account_id = str(data.get("to_account_id", "")).strip()
    amount_raw = str(data.get("amount", "")).strip()

    val_target, err_target = validate_account_number(to_account_id)
    if not val_target:
        return jsonify({"success": False, "message": err_target}), 400

    val_amt, amount, err_amt = validate_amount(amount_raw)
    if not val_amt or amount is None:
        return jsonify({"success": False, "message": err_amt}), 400

    success, new_bal, msg = atm_service.transfer(from_account_id, to_account_id, amount)
    if success:
        return jsonify({"success": True, "new_balance": new_bal, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@app.route("/api/customer/history/<account_id>", methods=["GET"])
def customer_history(account_id):
    history = txn_service.get_account_history(account_id)
    return jsonify({
        "success": True,
        "transactions": [t.to_dict() for t in history]
    })


@app.route("/api/customer/change-pin", methods=["POST"])
def customer_change_pin():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    old_pin = str(data.get("old_pin", "")).strip()
    new_pin = str(data.get("new_pin", "")).strip()

    val_pin, err_pin = validate_pin(new_pin)
    if not val_pin:
        return jsonify({"success": False, "message": err_pin}), 400

    success, msg = atm_service.change_pin(account_id, old_pin, new_pin)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


# =========================================================================
# ADMIN API ENDPOINTS
# =========================================================================

@app.route("/api/auth/login/admin", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    success, admin, msg = auth_service.authenticate_admin(username, password)
    if success and admin:
        return jsonify({
            "success": True,
            "message": msg,
            "admin": {"username": admin.username, "admin_id": admin.admin_id}
        })
    return jsonify({"success": False, "message": msg}), 401


@app.route("/api/admin/accounts", methods=["GET"])
def admin_get_accounts():
    accounts = admin_service.get_all_accounts()
    return jsonify({
        "success": True,
        "accounts": [a.to_dict() for a in accounts]
    })


@app.route("/api/admin/accounts/create", methods=["POST"])
def admin_create_account():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    name = str(data.get("name", "")).strip()
    pin = str(data.get("pin", "")).strip()
    init_dep_raw = str(data.get("initial_deposit", "0")).strip() or "0"

    val_acc, err_acc = validate_account_number(account_id)
    if not val_acc:
        return jsonify({"success": False, "message": err_acc}), 400

    val_name, err_name = validate_name(name)
    if not val_name:
        return jsonify({"success": False, "message": err_name}), 400

    val_pin, err_pin = validate_pin(pin)
    if not val_pin:
        return jsonify({"success": False, "message": err_pin}), 400

    init_dep = 0.0
    if init_dep_raw:
        try:
            dep_float = float(init_dep_raw)
            if dep_float < 0:
                return jsonify({"success": False, "message": "Initial deposit cannot be negative."}), 400
            elif dep_float > 0:
                val_dep, amt, err_dep = validate_amount(init_dep_raw)
                if not val_dep or amt is None:
                    return jsonify({"success": False, "message": err_dep}), 400
                init_dep = amt
        except ValueError:
            return jsonify({"success": False, "message": "Invalid initial deposit amount."}), 400

    success, msg = admin_service.create_account(account_id, name, pin, init_dep)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@app.route("/api/admin/accounts/block", methods=["POST"])
def admin_block_account():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    success, msg = admin_service.block_account(account_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@app.route("/api/admin/accounts/unblock", methods=["POST"])
def admin_unblock_account():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    success, msg = admin_service.unblock_account(account_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@app.route("/api/admin/accounts/delete", methods=["POST"])
def admin_delete_account():
    data = request.get_json() or {}
    account_id = str(data.get("account_id", "")).strip()
    success, msg = admin_service.delete_account(account_id)
    if success:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "message": msg}), 400


@app.route("/api/admin/transactions", methods=["GET"])
def admin_get_transactions():
    transactions = txn_service.get_all_transactions()
    return jsonify({
        "success": True,
        "transactions": [t.to_dict() for t in transactions]
    })


@app.route("/api/admin/metrics", methods=["GET"])
def admin_get_metrics():
    accounts = admin_service.get_all_accounts()
    transactions = txn_service.get_all_transactions()
    total_reserve = admin_service.get_total_bank_reserve()

    active_cnt = sum(1 for a in accounts if a.status == "active")
    blocked_cnt = sum(1 for a in accounts if a.status in ("blocked", "locked"))

    return jsonify({
        "success": True,
        "metrics": {
            "total_accounts": len(accounts),
            "active_accounts": active_cnt,
            "blocked_accounts": blocked_cnt,
            "total_transactions": len(transactions),
            "total_reserve": total_reserve,
            "currency_symbol": CURRENCY_SYMBOL
        }
    })


@app.route("/api/admin/reports/generate", methods=["POST"])
def admin_generate_reports():
    daily_txt, csv_path = admin_service.generate_reports()
    return jsonify({
        "success": True,
        "message": "Reports generated successfully!",
        "daily_txt_url": "/reports/daily_report.txt",
        "csv_url": "/reports/transaction_report.csv"
    })


@app.route("/reports/<path:filename>")
def download_report(filename):
    return send_from_directory(str(REPORTS_DIR), filename, as_attachment=True)


if __name__ == "__main__":
    print("[START] Starting ATM Simulation Web Application on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
