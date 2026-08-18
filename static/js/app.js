/**
 * ATM SIMULATION & DIGITAL BANKING SYSTEM - FRONTEND APP
 * Handles UI interactions, PIN keypad, API calls, and SPA navigation.
 */

// Application State
let activeAccount = null;
let activeAdmin = null;
let currentPortal = 'customer';
let activeLoginField = 'cust-account-id';
let pinKeypadBuffer = "";

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    startClock();
    checkActiveSession();
    setupKeypadTargeting();
});

// Live Header Clock
function startClock() {
    const clockEl = document.getElementById("live-clock");
    setInterval(() => {
        const now = new Date();
        const formatted = now.toLocaleDateString('en-GB') + " " + now.toLocaleTimeString();
        if (clockEl) clockEl.textContent = formatted;
    }, 1000);
}

// Session check - Restores Bank Admin session on refresh; Customer login remains mandatory on start
function checkActiveSession() {
    const savedAdmin = localStorage.getItem("atm_admin");
    const activePortal = localStorage.getItem("active_portal");

    if (savedAdmin && activePortal === "admin") {
        try {
            activeAdmin = JSON.parse(savedAdmin);
            switchPortal('admin');
            showAdminView("admin-dashboard-view");
            fetchAdminMetrics();
            fetchAdminAccounts();
            return;
        } catch (e) {
            localStorage.removeItem("atm_admin");
            localStorage.removeItem("active_portal");
        }
    }

    activeAccount = null;
    localStorage.removeItem("atm_account");
    showCustomerView("customer-login-view");
}

// Portal Switcher
function switchPortal(portal) {
    currentPortal = portal;
    localStorage.setItem("active_portal", portal);
    const custBtn = document.getElementById("nav-customer-btn");
    const adminBtn = document.getElementById("nav-admin-btn");
    const custSection = document.getElementById("customer-portal");
    const adminSection = document.getElementById("admin-portal");

    if (portal === 'customer') {
        custBtn.classList.add("active");
        adminBtn.classList.remove("active");
        custSection.classList.remove("hidden");
        adminSection.classList.add("hidden");
    } else {
        adminBtn.classList.add("active");
        custBtn.classList.remove("active");
        adminSection.classList.remove("hidden");
        custSection.classList.add("hidden");
        if (activeAdmin) {
            showAdminView("admin-dashboard-view");
            fetchAdminMetrics();
            fetchAdminAccounts();
        } else {
            showAdminView("admin-login-view");
        }
    }
}

// Show/Hide Customer Subviews
function showCustomerView(viewId) {
    document.getElementById("customer-login-view").classList.add("hidden");
    document.getElementById("customer-dashboard-view").classList.add("hidden");
    document.getElementById(viewId).classList.remove("hidden");
}

// Show/Hide Admin Subviews
function showAdminView(viewId) {
    document.getElementById("admin-login-view").classList.add("hidden");
    document.getElementById("admin-dashboard-view").classList.add("hidden");
    document.getElementById(viewId).classList.remove("hidden");
}

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check";
    if (type === "error") icon = "fa-circle-exclamation";

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Quick Demo Account Auto-Fill
function fillCustomerDemo(accId, pin) {
    document.getElementById("cust-account-id").value = accId;
    document.getElementById("cust-pin").value = pin;
    activeLoginField = 'cust-pin';
    document.getElementById("cust-pin").focus();
}

function fillAdminDemo() {
    document.getElementById("admin-user").value = "admin";
    document.getElementById("admin-pass").value = "admin123";
}

// Setup input listeners to track active field and auto-advance focus
function setupKeypadTargeting() {
    const accInput = document.getElementById("cust-account-id");
    const pinInput = document.getElementById("cust-pin");

    if (accInput) {
        accInput.addEventListener("focus", () => { activeLoginField = 'cust-account-id'; });
        accInput.addEventListener("input", () => {
            if (accInput.value.length >= 4 && pinInput) {
                pinInput.focus();
                activeLoginField = 'cust-pin';
            }
        });
    }
    if (pinInput) {
        pinInput.addEventListener("focus", () => { activeLoginField = 'cust-pin'; });
    }
}

// Smart Keypad press handler for both Account ID & PIN
function pressKeypad(key) {
    const accInput = document.getElementById("cust-account-id");
    const pinInput = document.getElementById("cust-pin");
    if (!accInput || !pinInput) return;

    if (key === 'clear') {
        if (activeLoginField === 'cust-pin' && pinInput.value.length > 0) {
            pinInput.value = "";
        } else {
            accInput.value = "";
            accInput.focus();
            activeLoginField = 'cust-account-id';
        }
    } else if (key === 'enter') {
        const form = document.getElementById("customer-login-form");
        if (form) form.requestSubmit();
    } else {
        // Digit (0-9) pressed
        // If Account ID is not yet 4 digits or is currently active field
        if (activeLoginField === 'cust-account-id' || accInput.value.length < 4) {
            if (accInput.value.length < 4) {
                accInput.value += key;
            }
            if (accInput.value.length >= 4) {
                pinInput.focus();
                activeLoginField = 'cust-pin';
            }
        } else {
            if (pinInput.value.length < 8) {
                pinInput.value += key;
            }
        }
    }
}

// =========================================================================
// CUSTOMER API CALLS
// =========================================================================

async function handleCustomerLogin(event) {
    event.preventDefault();
    const account_id = document.getElementById("cust-account-id").value.trim();
    const pin = document.getElementById("cust-pin").value.trim();

    try {
        const res = await fetch("/api/auth/login/customer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id, pin })
        });
        const data = await res.json();

        if (data.success) {
            activeAccount = data.account;
            refreshCustomerDashboard();
            showCustomerView("customer-dashboard-view");
            showToast(data.message, "success");
            pinKeypadBuffer = "";
            document.getElementById("cust-pin").value = "";
        } else {
            showToast(data.message, "error");
            pinKeypadBuffer = "";
            document.getElementById("cust-pin").value = "";
        }
    } catch (err) {
        showToast("Server communication error", "error");
    }
}

async function refreshCustomerDashboard() {
    if (!activeAccount) return;

    try {
        const res = await fetch(`/api/customer/account/${activeAccount.account_id}`);
        const data = await res.json();

        if (data.success) {
            activeAccount = data.account;

            document.getElementById("card-acc-num").textContent = `•••• ${activeAccount.account_id}`;
            document.getElementById("card-holder-name").textContent = activeAccount.name.toUpperCase();
            document.getElementById("card-status-badge").textContent = activeAccount.status.toUpperCase();
            document.getElementById("cust-balance-display").textContent = `₹${activeAccount.balance.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        }
    } catch (e) {
        console.error("Dashboard refresh error:", e);
    }
}

function logoutCustomer() {
    activeAccount = null;
    localStorage.removeItem("atm_account");
    showCustomerView("customer-login-view");
    showToast("Successfully logged out from ATM", "info");
}

// Preset cash withdraw selection
function setWithdrawPreset(amount) {
    document.getElementById("withdraw-amount").value = amount;
}

// Cash Withdrawal
async function handleWithdrawSubmit(event) {
    event.preventDefault();
    if (!activeAccount) return;

    const amount = parseFloat(document.getElementById("withdraw-amount").value);
    try {
        const res = await fetch("/api/customer/withdraw", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id: activeAccount.account_id, amount })
        });
        const data = await res.json();

        if (data.success) {
            closeModal('modal-withdraw');
            showToast(data.message, "success");
            refreshCustomerDashboard();
            document.getElementById("withdraw-amount").value = "";
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("Transaction failed", "error");
    }
}

// Deposit
async function handleDepositSubmit(event) {
    event.preventDefault();
    if (!activeAccount) return;

    const amount = parseFloat(document.getElementById("deposit-amount").value);
    try {
        const res = await fetch("/api/customer/deposit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id: activeAccount.account_id, amount })
        });
        const data = await res.json();

        if (data.success) {
            closeModal('modal-deposit');
            showToast(data.message, "success");
            refreshCustomerDashboard();
            document.getElementById("deposit-amount").value = "";
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("Deposit failed", "error");
    }
}

// Transfer
async function handleTransferSubmit(event) {
    event.preventDefault();
    if (!activeAccount) return;

    const to_account_id = document.getElementById("transfer-target-id").value.trim();
    const amount = parseFloat(document.getElementById("transfer-amount").value);

    try {
        const res = await fetch("/api/customer/transfer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ from_account_id: activeAccount.account_id, to_account_id, amount })
        });
        const data = await res.json();

        if (data.success) {
            closeModal('modal-transfer');
            showToast(data.message, "success");
            refreshCustomerDashboard();
            document.getElementById("transfer-target-id").value = "";
            document.getElementById("transfer-amount").value = "";
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("Transfer failed", "error");
    }
}

// Change PIN
async function handleChangePinSubmit(event) {
    event.preventDefault();
    if (!activeAccount) return;

    const old_pin = document.getElementById("pin-old").value.trim();
    const new_pin = document.getElementById("pin-new").value.trim();
    const confirm_pin = document.getElementById("pin-confirm").value.trim();

    if (new_pin !== confirm_pin) {
        showToast("New PIN and Confirm PIN do not match!", "error");
        return;
    }

    try {
        const res = await fetch("/api/customer/change-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id: activeAccount.account_id, old_pin, new_pin })
        });
        const data = await res.json();

        if (data.success) {
            closeModal('modal-pin');
            showToast(data.message, "success");
            document.getElementById("pin-old").value = "";
            document.getElementById("pin-new").value = "";
            document.getElementById("pin-confirm").value = "";
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("PIN change failed", "error");
    }
}

// Transaction History Receipt
async function fetchCustomerHistory() {
    if (!activeAccount) return;

    try {
        const res = await fetch(`/api/customer/history/${activeAccount.account_id}`);
        const data = await res.json();

        if (data.success) {
            const container = document.getElementById("receipt-items-container");
            container.innerHTML = "";

            const now = new Date();
            const formattedDate = now.toLocaleDateString('en-GB') + " " + now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

            document.getElementById("receipt-datetime").textContent = formattedDate;
            document.getElementById("receipt-acc-id").textContent = `•••• ${activeAccount.account_id}`;
            document.getElementById("receipt-holder").textContent = activeAccount.name.toUpperCase();
            document.getElementById("receipt-final-bal").textContent = `₹${activeAccount.balance.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

            if (data.transactions.length === 0) {
                container.innerHTML = "<div style='text-align:center; padding:1rem; color:#64748b;'>No transaction history records found.</div>";
            } else {
                data.transactions.forEach(t => {
                    const row = document.createElement("div");
                    row.className = "receipt-table-row";
                    const isCredit = t.type === 'DEPOSIT' || t.type === 'TRANSFER_IN';
                    const typeClass = isCredit ? 'credit' : 'debit';
                    const symbol = isCredit ? '+' : '-';

                    let timeStr = t.timestamp;
                    try {
                        const parts = t.timestamp.split(" ");
                        if (parts.length >= 2) {
                            const dParts = parts[0].split("-");
                            const tParts = parts[1].split(":");
                            if (dParts.length === 3 && tParts.length >= 2) {
                                timeStr = `${dParts[2]}/${dParts[1]} ${tParts[0]}:${tParts[1]}`;
                            }
                        }
                    } catch (e) {}

                    row.innerHTML = `
                        <span class="cell-time">${timeStr}</span>
                        <span class="cell-type ${typeClass}">${t.type}</span>
                        <span class="cell-amount ${typeClass} text-right">${symbol}₹${t.amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
                        <span class="cell-bal text-right">₹${t.balance_after.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
                    `;
                    container.appendChild(row);
                });
            }
            openModal('modal-history');
        }
    } catch (err) {
        showToast("Failed to fetch transaction history", "error");
    }
}

// =========================================================================
// ADMIN API CALLS
// =========================================================================

async function handleAdminLogin(event) {
    event.preventDefault();
    const username = document.getElementById("admin-user").value.trim();
    const password = document.getElementById("admin-pass").value.trim();

    try {
        const res = await fetch("/api/auth/login/admin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();

        if (data.success) {
            activeAdmin = data.admin;
            localStorage.setItem("atm_admin", JSON.stringify(activeAdmin));
            localStorage.setItem("active_portal", "admin");
            showAdminView("admin-dashboard-view");
            fetchAdminMetrics();
            fetchAdminAccounts();
            showToast(data.message, "success");
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("Admin login failed", "error");
    }
}

function logoutAdmin() {
    activeAdmin = null;
    localStorage.removeItem("atm_admin");
    localStorage.removeItem("active_portal");
    showAdminView("admin-login-view");
    showToast("Logged out from Admin Panel", "info");
}

async function fetchAdminMetrics() {
    try {
        const res = await fetch("/api/admin/metrics");
        const data = await res.json();
        if (data.success) {
            const m = data.metrics;
            document.getElementById("m-reserve").textContent = `₹${m.total_reserve.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
            document.getElementById("m-total-accounts").textContent = m.total_accounts;
            document.getElementById("m-active-accounts").textContent = m.active_accounts;
            document.getElementById("m-blocked-accounts").textContent = m.blocked_accounts;
        }
    } catch (e) {
        console.error("Admin metrics error:", e);
    }
}

async function fetchAdminAccounts() {
    try {
        const res = await fetch("/api/admin/accounts");
        const data = await res.json();
        if (data.success) {
            renderAdminAccountsTable(data.accounts);
        }
    } catch (e) {
        console.error("Fetch accounts error:", e);
    }
}

function renderAdminAccountsTable(accounts) {
    const tbody = document.getElementById("admin-accounts-tbody");
    tbody.innerHTML = "";

    accounts.forEach(a => {
        const tr = document.createElement("tr");
        const isLocked = a.status === 'locked' || a.status === 'blocked';
        const badgeClass = isLocked ? 'badge-locked' : 'badge-active';

        let actionBtns = "";
        if (isLocked) {
            actionBtns = `<button class="btn btn-success btn-sm" onclick="adminUnblockAccount('${a.account_id}')"><i class="fa-solid fa-lock-open"></i> Unblock</button>`;
        } else {
            if (a.failed_attempts > 0) {
                actionBtns += `<button class="btn btn-warning btn-sm" onclick="adminUnblockAccount('${a.account_id}')"><i class="fa-solid fa-rotate-left"></i> Reset Attempts</button> `;
            }
            actionBtns += `<button class="btn btn-outline-danger btn-sm" onclick="adminBlockAccount('${a.account_id}')"><i class="fa-solid fa-ban"></i> Block</button>`;
        }

        tr.innerHTML = `
            <td><strong>${a.account_id}</strong></td>
            <td>${a.name}</td>
            <td>₹${a.balance.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
            <td><span class="badge ${badgeClass}">${a.status.toUpperCase()}</span></td>
            <td>${a.failed_attempts}</td>
            <td>${a.created_at}</td>
            <td>
                ${actionBtns}
                <button class="btn btn-outline-danger btn-sm" onclick="adminDeleteAccount('${a.account_id}')"><i class="fa-solid fa-trash"></i> Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterAdminAccounts() {
    const query = document.getElementById("admin-search-input").value.toLowerCase();
    const rows = document.querySelectorAll("#admin-accounts-tbody tr");
    rows.forEach(tr => {
        const text = tr.textContent.toLowerCase();
        tr.style.display = text.includes(query) ? "" : "none";
    });
}

async function adminBlockAccount(account_id) {
    try {
        const res = await fetch("/api/admin/accounts/block", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id })
        });
        const data = await res.json();
        showToast(data.message, data.success ? "success" : "error");
        fetchAdminAccounts();
        fetchAdminMetrics();
    } catch (e) {
        showToast("Action failed", "error");
    }
}

async function adminUnblockAccount(account_id) {
    try {
        const res = await fetch("/api/admin/accounts/unblock", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id })
        });
        const data = await res.json();
        showToast(data.message, data.success ? "success" : "error");
        fetchAdminAccounts();
        fetchAdminMetrics();
    } catch (e) {
        showToast("Action failed", "error");
    }
}

async function adminDeleteAccount(account_id) {
    if (!confirm(`Are you sure you want to permanently delete account ${account_id}?`)) return;

    try {
        const res = await fetch("/api/admin/accounts/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id })
        });
        const data = await res.json();
        showToast(data.message, data.success ? "success" : "error");
        fetchAdminAccounts();
        fetchAdminMetrics();
    } catch (e) {
        showToast("Delete failed", "error");
    }
}

async function handleAdminCreateAccount(event) {
    event.preventDefault();
    const account_id = document.getElementById("new-acc-id").value.trim();
    const name = document.getElementById("new-acc-name").value.trim();
    const pin = document.getElementById("new-acc-pin").value.trim();
    const initial_deposit = document.getElementById("new-acc-deposit").value.trim() || "0";

    try {
        const res = await fetch("/api/admin/accounts/create", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_id, name, pin, initial_deposit })
        });
        const data = await res.json();

        if (data.success) {
            showToast(data.message, "success");
            document.getElementById("admin-create-form").reset();
            fetchAdminAccounts();
            fetchAdminMetrics();
            switchAdminTab('accounts-tab');
        } else {
            showToast(data.message, "error");
        }
    } catch (err) {
        showToast("Create account failed", "error");
    }
}

async function fetchAdminTransactions() {
    try {
        const res = await fetch("/api/admin/transactions");
        const data = await res.json();
        if (data.success) {
            const tbody = document.getElementById("admin-transactions-tbody");
            tbody.innerHTML = "";
            data.transactions.forEach(t => {
                const tr = document.createElement("tr");
                const isCredit = t.type === 'DEPOSIT' || t.type === 'TRANSFER_IN';
                const typeColor = isCredit ? 'var(--color-success)' : 'var(--color-danger)';

                tr.innerHTML = `
                    <td><code>${t.transaction_id}</code></td>
                    <td><strong>${t.account_id}</strong></td>
                    <td><span style="color:${typeColor}; font-weight:bold;">${t.type}</span></td>
                    <td>₹${t.amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                    <td>₹${t.balance_after.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                    <td>${t.timestamp}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error("Audit log error:", e);
    }
}

function switchAdminTab(tabId, clickedBtn = null) {
    const tabs = document.querySelectorAll(".admin-tab-content");
    const btns = document.querySelectorAll(".tab-btn");
    tabs.forEach(t => t.classList.add("hidden"));
    btns.forEach(b => b.classList.remove("active"));

    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.remove("hidden");

    let activeBtn = clickedBtn;
    if (!activeBtn && typeof event !== "undefined" && event && event.currentTarget && event.currentTarget.classList && event.currentTarget.classList.contains("tab-btn")) {
        activeBtn = event.currentTarget;
    }
    if (!activeBtn) {
        btns.forEach(b => {
            if (b.getAttribute("onclick") && b.getAttribute("onclick").includes(`'${tabId}'`)) {
                activeBtn = b;
            }
        });
    }
    if (activeBtn) activeBtn.classList.add("active");

    if (tabId === 'audit-tab') fetchAdminTransactions();
    if (tabId === 'accounts-tab') fetchAdminAccounts();
}

async function generateAdminReports() {
    try {
        const res = await fetch("/api/admin/reports/generate", { method: "POST" });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, "success");
            const linksDiv = document.getElementById("reports-download-links");
            document.getElementById("link-txt-report").href = data.daily_txt_url;
            document.getElementById("link-csv-report").href = data.csv_url;
            linksDiv.classList.remove("hidden");
        } else {
            showToast("Report generation failed", "error");
        }
    } catch (e) {
        showToast("Error generating reports", "error");
    }
}

// Modal Control
function openModal(modalId) {
    document.getElementById(modalId).classList.remove("hidden");
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add("hidden");
}
