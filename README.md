# 🏧 Reserve Bank of India - ATM Simulation System (Web Browser GUI)

> 👨‍💻 **Author**: **Himanshu Dobariya**  
> 🔗 **GitHub Profile**: [@himanshudobariya7777](https://github.com/himanshudobariya7777)  
> 📦 **GitHub Repository**: [https://github.com/himanshudobariya7777/ATM-Simulation](https://github.com/himanshudobariya7777/ATM-Simulation)

A production-grade, modular, Object-Oriented Python ATM Simulation system featuring a **modern Web Browser GUI Application** (`app.py`), REST API backend (`Flask`), SQLite persistence, PBKDF2-HMAC-SHA256 salted PIN security, automatic 3-attempt account lockout protection, strict banking rules, multi-account fund transfers, administrative management, automated report generation (TXT/CSV), and a unit test suite.

---

## 🚀 Virtual Environment (`atm`) & Quick Start Guide

### Step 1: Create Virtual Environment (`atm`)
Create the Python virtual environment named `atm`:

```bash
python -m venv atm
```

### Step 2: Activate Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .\atm\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  atm\Scripts\activate.bat
  ```
- **Linux / macOS**:
  ```bash
  source atm/bin/activate
  ```

### Step 3: Install Required Dependencies
Install Flask and Pytest inside the `atm` virtual environment:

```bash
pip install -r requirements.txt
```

### Step 4: Launch the Web Application
Start the Flask application server:

```bash
python app.py
```

### Step 5: Open in Web Browser
Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Step 6: Run Automated Unit Tests (Optional)
Run pytest inside the virtual environment:

```bash
python -m pytest tests/
```

---

## 🔑 Pre-Seeded Default Credentials

When launched for the first time, SQLite automatically creates `database/atm.db` and seeds 20 sample customer accounts:

### 👨‍💼 Bank Admin Access
- **Admin Username**: `admin`
- **Admin Password**: `admin123`

### 👤 20 Sample Customer Accounts (4-Digit ID / 8-Digit PIN / ₹20,00,000.00 Balance)

| Account ID | Holder Name | Default PIN | Initial Balance | Account Status |
| :--- | :--- | :--- | :--- | :--- |
| `1001` | Himanshu | `12345678` | ₹20,00,000.00 | Active |
| `1002` | Rahul | `87654321` | ₹20,00,000.00 | Active |
| `1003` | Jay | `11223344` | ₹20,00,000.00 | Active |
| `1004` | Priya | `55667788` | ₹20,00,000.00 | Active |
| `1005` | Anish | `99887766` | ₹20,00,000.00 | Active |
| `1006` | Sneha | `11112222` | ₹20,00,000.00 | Active |
| `1007` | Amit | `33334444` | ₹20,00,000.00 | Active |
| `1008` | Pooja | `55556666` | ₹20,00,000.00 | Active |
| `1009` | Rohan | `77778888` | ₹20,00,000.00 | Active |
| `1010` | Kavya | `99990000` | ₹20,00,000.00 | Active |
| `1011` | Vikas | `12121212` | ₹20,00,000.00 | Active |
| `1012` | Neha | `34343434` | ₹20,00,000.00 | Active |
| `1013` | Suresh | `56565656` | ₹20,00,000.00 | Active |
| `1014` | Ritu | `78787878` | ₹20,00,000.00 | Active |
| `1015` | Deepak | `90909090` | ₹20,00,000.00 | Active |
| `1016` | Divya | `13579246` | ₹20,00,000.00 | Active |
| `1017` | Manoj | `24681357` | ₹20,00,000.00 | Active |
| `1018` | Swati | `98765432` | ₹20,00,000.00 | Active |
| `1019` | Alok | `87651234` | ₹20,00,000.00 | Active |
| `1020` | Meera | `43218765` | ₹20,00,000.00 | Active |

---

## 🌟 Web GUI Highlights & Features

- **Single Page Application (SPA)**: Powered by Flask REST API and HTML5/CSS3/JavaScript.
- **Visual ATM Kiosk Screen**:
  - Interactive numeric PIN keypad (`1-9, 0, Clear, Enter`).
  - **Quick Demo Account Chips**: 1-click auto-fill for sample accounts.
- **Customer Banking Dashboard**:
  - Metallic virtual credit card preview with balance badge and status indicator.
  - **Quick Cash Withdrawal Presets**: Buttons for `₹500`, `₹1,000`, `₹2,000`, `₹5,000`, `₹10,000`, `₹20,000` + custom input.
  - **Cash Deposit Modal**: Deposit funds instantly.
  - **Fund Transfer Modal**: Transfer money to any valid recipient account.
  - **Printable Thermal Receipt Modal**: Itemized transaction history printout.
  - **PIN Change Modal**: Update security PIN.
- **Admin Control Panel**:
  - Executive summary metrics cards: Total Bank Reserve, Total Accounts, Active Accounts, Blocked Accounts.
  - Customer Accounts table with instant search filter, block/unblock toggles, and delete actions.
  - Register New Account form.
  - System-wide Transaction Audit Log table.
  - **1-Click Report Generator**: Export and download `daily_report.txt` and `transaction_report.csv`.

---

## 💰 Banking Rules & Limits (INR ₹)

- **Minimum Withdrawal**: ₹100.00 per transaction
- **Maximum Single Withdrawal**: ₹20,000.00 per transaction
- **Daily Cumulative Withdrawal Limit**: ₹50,000.00 per calendar day
- **Fund Transfers**: Atomic transaction logic (deducts sender, credits recipient, logs `TRANSFER_OUT` and `TRANSFER_IN`).
- **Account Lockout**: After **3 consecutive failed PIN attempts**, account status changes to `LOCKED`.

---

## 🧱 Project Directory Architecture

```
ATM_Simulation/
│
├── app.py                     # Flask Web Application & REST API Entry Point
├── config.py                  # Global settings, paths, limits, and constants
├── requirements.txt            # Python dependencies (flask, pytest)
├── README.md                  # Project documentation
├── atm_app.log                # System application log file
│
├── templates/                 # HTML Templates for Web GUI
│   └── index.html             # Single Page Web Application UI
│
├── static/                    # Web GUI Static Assets
│   ├── css/
│   │   └── style.css          # Glassmorphism dark mode CSS design system
│   └── js/
│       └── app.js              # SPA frontend controller & API calls
│
├── database/
│   ├── atm.db                 # SQLite database file
│   └── db_manager.py          # SQLite connection manager, DDL tables, and data seeder
│
├── models/
│   ├── account.py             # Customer Account domain dataclass
│   ├── transaction.py         # Transaction log domain dataclass
│   └── admin.py               # Admin user domain dataclass
│
├── services/
│   ├── auth_service.py        # Authentication & 3-attempt account lockout logic
│   ├── atm_service.py         # Core banking operations (withdraw, deposit, transfer, pin change)
│   ├── transaction_service.py # Transaction logging and history retrieval
│   └── admin_service.py       # Admin management & TXT/CSV report generator
│
├── utils/
│   ├── security.py            # PBKDF2-HMAC-SHA256 PIN/password hashing & verification
│   ├── validators.py          # Input validation for accounts, PINs, names, and amounts
│   ├── helpers.py             # Currency formatting (₹), timestamping, ID generator
│   └── logger.py              # Application logger setup
│
├── reports/                   # Output directory for exported reports
│   ├── daily_report.txt       # Daily summary text report
│   └── transaction_report.csv # System-wide CSV transaction audit log
│
└── tests/                     # Pytest Unit Test Suite
    ├── __init__.py
    ├── test_auth.py           # Authentication, PIN checks, & lockout tests
    ├── test_atm.py            # Deposit, withdrawal rules, & daily limit tests
    └── test_transactions.py   # Fund transfers & audit history tests
```

---

## 📊 System Reports & Data Export

Generating reports in the Admin Panel creates:
1. `reports/daily_report.txt`: Summary of total accounts, active/blocked breakdowns, total bank reserves, deposits, withdrawals, and transfer metrics.
2. `reports/transaction_report.csv`: Complete CSV spreadsheet dump containing `Transaction ID`, `Account ID`, `Type`, `Amount`, `Balance After`, and `Timestamp`.
