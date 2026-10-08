# 🛒 SecureShop — Red Team / Application Security Lab

> **Educational Security Lab** | OWASP Top 10 Demonstration | Python Flask + SQLite

[![OWASP Top 10](https://img.shields.io/badge/OWASP-Top%2010-red)](https://owasp.org/Top10/)
[![Flask](https://img.shields.io/badge/Flask-3.0-blue)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

> ⚠️ **IMPORTANT DISCLAIMER**
> The `vulnerable_version` folder contains **intentionally vulnerable code** for educational purposes only.
> **Do NOT deploy the vulnerable version publicly.** It is designed to run on `localhost` only.
> This project is created for a college cybersecurity assignment demonstrating the **BUILD → SCAN → INVESTIGATE → FIX → RETEST** methodology.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Project Structure](#-project-structure)
- [Vulnerabilities Demonstrated](#-vulnerabilities-demonstrated)
- [Quick Start](#-quick-start)
- [Running the Vulnerable Version](#-running-the-vulnerable-version)
- [Running the Fixed Version](#-running-the-fixed-version)
- [OWASP ZAP Scanning](#-owasp-zap-scanning)
- [Testing Guide](#-testing-guide)
- [Screenshots Required](#-screenshots-required)
- [Git Push to GitHub](#-git-push-to-github)
- [Documentation Index](#-documentation-index)

---

## 🎯 Project Overview

**SecureShop** is a fully functional e-commerce web application built with Python Flask and SQLite, created as a cybersecurity assignment to demonstrate the **Build → Scan → Investigate → Fix → Retest** methodology.

The project exists in **two versions**:

| Version | Port | Description |
|---------|------|-------------|
| `vulnerable_version/` | 5000 | Intentionally vulnerable — contains OWASP Top 10 issues |
| `fixed_version/`      | 5001 | All vulnerabilities properly remediated |

### Features
- 🏠 Home page with featured products
- 👤 User registration, login, and profile
- 🔍 Product search and detail pages
- 🛒 Shopping cart and checkout
- 📦 Order history
- ⚙️ Admin panel (product management + user listing)

---

## 📁 Project Structure

```
SecureShop/
├── vulnerable_version/          # ⚠️ INTENTIONALLY VULNERABLE
│   ├── app.py                   # Main Flask app with vulnerabilities
│   ├── schema.sql               # Database schema + seed data (MD5 passwords)
│   ├── requirements.txt         # Includes outdated Werkzeug 2.0.3
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── search.html
│   │   ├── product_detail.html
│   │   ├── cart.html
│   │   ├── profile.html
│   │   ├── orders.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       ├── add_product.html
│   │       ├── edit_product.html
│   │       └── users.html
│   └── static/
│       ├── css/style.css
│       └── js/main.js
│
├── fixed_version/               # ✅ REMEDIATED VERSION
│   ├── app.py                   # Flask app with all fixes applied
│   ├── schema_fixed.sql         # Schema with bcrypt password hashes
│   ├── init_db.py               # Script to generate fresh bcrypt DB
│   ├── requirements.txt         # Updated secure dependencies
│   └── templates/               # Same structure, updated content
│
├── docs/
│   ├── vulnerability_documentation.md
│   ├── remediation_report.md
│   ├── retest_report.md
│   └── zap_scanning_guide.md
│
├── evidence/                    # Screenshots go here (see below)
│   └── README.md
│
├── tests/
│   ├── test_vulnerable.py
│   └── test_fixed.py
│
├── .gitignore
└── README.md                    ← You are here
```

---

## 🔓 Vulnerabilities Demonstrated

| # | OWASP ID | Vulnerability | Location | Severity |
|---|----------|---------------|----------|----------|
| 1 | **A01** | Broken Access Control | `/admin` routes — no role check | 🔴 High |
| 2 | **A03** | SQL Injection | `/search?q=` parameter | 🔴 Critical |
| 3 | **A05** | Security Misconfiguration | `DEBUG=True`, exposed `/debug/config` | 🔴 High |
| 4 | **A07** | Auth/Session Weakness | MD5 hashing, no rate limiting | 🔴 High |
| 5 | **A06** | Vulnerable Components | Werkzeug 2.0.3 (CVE-2023-25577) | 🟡 Medium |

See [`docs/vulnerability_documentation.md`](docs/vulnerability_documentation.md) for full details.

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- pip
- (For scanning) OWASP ZAP 2.14+

---

## 🚨 Running the Vulnerable Version

```bash
# 1. Navigate to the vulnerable version
cd SecureShop/vulnerable_version

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 3. Install dependencies (includes outdated Werkzeug)
pip install -r requirements.txt

# 4. Run the app — database is auto-created on first run
python app.py
```

> 🌐 Open http://localhost:5000

**Demo credentials:**
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| User | `alice` | `123456` |
| User | `bob` | `123456` |

### Testing Vulnerability A03 — SQL Injection
In the search box, try:
```
' OR '1'='1
' UNION SELECT id,username,password,email,role,created_at FROM users--
```

### Testing Vulnerability A01 — Broken Access Control
1. Login as `alice` (regular user)
2. Navigate directly to `http://localhost:5000/admin`
3. You'll see the admin panel — **no 403 is returned**

### Testing Vulnerability A05 — Security Misconfiguration
- Visit: `http://localhost:5000/debug/config`
- Observe: secret key, database path, all environment variables exposed

---

## ✅ Running the Fixed Version

```bash
# 1. Navigate to the fixed version
cd SecureShop/fixed_version

# 2. Create a virtual environment (separate from vulnerable)
python -m venv venv
venv\Scripts\activate

# 3. Install updated dependencies
pip install -r requirements.txt

# 4. Initialise the database with fresh bcrypt hashes
python init_db.py

# 5. Run the fixed app
python app.py
```

> 🌐 Open http://localhost:5001

**Demo credentials:**
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@Secure2026` |
| User | `alice` | `Alice@2026` |

### Verifying Fixes
1. **A01**: Login as `alice`, go to `http://localhost:5001/admin` → should get **403 Forbidden**
2. **A03**: Try SQL injection in search → results are safely escaped
3. **A05**: `/debug/config` does not exist (404)
4. **A07**: Try logging in 6 times rapidly → **429 Too Many Requests**

---

## 🔍 OWASP ZAP Scanning

See [`docs/zap_scanning_guide.md`](docs/zap_scanning_guide.md) for full step-by-step instructions.

**Quick overview:**
1. Download OWASP ZAP from https://zaproxy.org
2. Set your browser to proxy through `localhost:8080`
3. Spider the vulnerable version at `http://localhost:5000`
4. Run Active Scan
5. Export HTML/XML report → save to `evidence/zap_scan_vulnerable.html`
6. Repeat on fixed version at `http://localhost:5001`
7. Save to `evidence/zap_scan_fixed.html`

---

## 🧪 Testing Guide

```bash
# Run tests for vulnerable version
cd SecureShop
pip install pytest
pytest tests/test_vulnerable.py -v

# Run tests for fixed version
pytest tests/test_fixed.py -v
```

---

## 📸 Screenshots Required

Place all screenshots in the `evidence/` folder. See [`evidence/README.md`](evidence/README.md) for the complete list of required screenshots.

**Key screenshots needed:**
1. Vulnerable home page running
2. SQL injection payload in search returning all users
3. `/debug/config` exposing secret key
4. Regular user accessing `/admin` (A01)
5. OWASP ZAP scan running on vulnerable version
6. ZAP scan report showing vulnerabilities found
7. Fixed version returning 403 on `/admin`
8. Fixed version — 429 rate limit response
9. ZAP scan on fixed version (reduced/no findings)

---

## 🚀 Git Push to GitHub

```bash
# 1. Initialise git repository (from SecureShop root)
cd SecureShop
git init

# 2. Add all files
git add .

# 3. First commit
git commit -m "Initial commit: SecureShop OWASP Lab (vulnerable + fixed versions)"

# 4. Create a new repo on GitHub (github.com → New Repository → name: SecureShop)

# 5. Connect and push
git remote add origin https://github.com/YOUR_USERNAME/SecureShop.git
git branch -M main
git push -u origin main

# 6. After adding evidence/screenshots:
git add evidence/
git commit -m "Add ZAP scan evidence and screenshots"
git push
```

> **Note:** The `.gitignore` excludes `*.db` (database files) and `__pycache__`. Do not commit database files to GitHub.

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [`docs/vulnerability_documentation.md`](docs/vulnerability_documentation.md) | Detailed write-up of each vulnerability |
| [`docs/remediation_report.md`](docs/remediation_report.md) | How each vulnerability was fixed |
| [`docs/retest_report.md`](docs/retest_report.md) | Retest results after fixes |
| [`docs/zap_scanning_guide.md`](docs/zap_scanning_guide.md) | Step-by-step ZAP scanning instructions |
| [`evidence/README.md`](evidence/README.md) | List of required screenshots/evidence |

---

## 📜 License

MIT License — for educational purposes only.

---

*SecureShop | Cybersecurity Assignment | OWASP Top 10 Lab | 2026*
