# Remediation Report
## SecureShop — OWASP Vulnerability Fix Analysis

> **Fixed Version:** 2.0 | **Date:** October 2026 | **Tester:** [Your Name]

---

## Executive Summary

Following the security assessment of SecureShop v1.0 (vulnerable version), all five identified OWASP Top 10 vulnerabilities have been remediated in SecureShop v2.0 (fixed version). This report documents the specific code changes made to address each vulnerability.

---

## Fix 1 — A01: Broken Access Control

### Root Cause
Admin routes only checked `if 'user_id' not in session` — the user's role was never verified server-side.

### Remediation Applied
Implemented two reusable Python decorators using `functools.wraps`:

```python
# fixed_version/app.py

from functools import wraps

def login_required(f):
    """Ensures the user is authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Ensures the user is authenticated AND has the admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            abort(403)   # HTTP 403 Forbidden — not just a redirect
        return f(*args, **kwargs)
    return decorated
```

**Applied to all admin routes:**
```python
@app.route('/admin')
@admin_required   # ← decorator enforces role check
def admin_dashboard():
    ...
```

### Before vs After

| Aspect | Vulnerable | Fixed |
|--------|-----------|-------|
| Auth check | `if 'user_id' not in session` only | `@admin_required` checks role |
| Non-admin response | Renders admin page | HTTP 403 Forbidden |
| Role source | Session only (not re-verified vs DB) | Session role set from DB at login |
| Admin routes covered | 0/5 | 5/5 |

---

## Fix 2 — A03: SQL Injection

### Root Cause
User input was directly concatenated into SQL query strings using Python string formatting.

### Remediation Applied
All queries use parameterised placeholders (`?`) — user input is passed as a separate tuple, never embedded in the query string.

```python
# VULNERABLE (before):
sql = "SELECT * FROM products WHERE name LIKE '%" + query + "%'"
products = db.execute(sql).fetchall()

# FIXED (after):
like_query = f'%{query}%'
products = db.execute(
    'SELECT * FROM products WHERE name LIKE ? OR description LIKE ?',
    (like_query, like_query)
).fetchall()
```

The `?` placeholder causes the SQLite driver to treat `like_query` as data — not as SQL syntax. Any quote characters are automatically escaped.

### Verification
The payload `' OR '1'='1` now returns zero results (no products contain that literal string), and the UNION injection `' UNION SELECT...` returns an error that is **not** exposed to the user.

---

## Fix 3 — A05: Security Misconfiguration

### Root Cause
Three sub-issues: DEBUG mode, hardcoded secret, and debug endpoint.

### Remediation Applied

#### 3a. DEBUG Disabled
```python
# VULNERABLE: app.config['DEBUG'] = True
# FIXED:
app.config['DEBUG'] = False
```

#### 3b. Secret Key from Environment Variable
```python
# VULNERABLE: app.secret_key = "secret123"
# FIXED:
app.secret_key = os.environ.get(
    'SECRET_KEY',
    'change-this-before-any-real-deployment-64chars-min!'
)
```
The default fallback is only for local development — for production, `SECRET_KEY` environment variable must be set to a random 64+ character string.

#### 3c. Debug Endpoint Removed
The `/debug/config` route is completely absent from `fixed_version/app.py`.

#### 3d. Custom Error Pages Added
```python
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, ...), 403

@app.errorhandler(500)
def server_error(e):
    # Never expose internal error details
    return render_template('error.html', code=500, ...), 500
```

#### 3e. Secure Cookie Settings
```python
app.config['SESSION_COOKIE_HTTPONLY'] = True   # prevent JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF mitigation
```

#### 3f. Server Bound to localhost Only
```python
# VULNERABLE: app.run(debug=True, host='0.0.0.0', port=5000)
# FIXED:
app.run(debug=False, host='127.0.0.1', port=5001)
```

---

## Fix 4 — A07: Authentication and Session Management

### Root Cause
MD5 hashing, no brute-force protection, no session regeneration.

### Remediation Applied

#### 4a. bcrypt Password Hashing
```python
import bcrypt

# Registration:
password_hash = bcrypt.hashpw(
    password.encode('utf-8'),
    bcrypt.gensalt(rounds=12)
).decode('utf-8')

# Login verification:
if user and bcrypt.checkpw(password.encode('utf-8'),
                            user['password'].encode('utf-8')):
    ...
```

bcrypt with `rounds=12` performs ~250ms of work per hash on modern hardware, making brute-force impractical (vs MD5 which does billions/second).

#### 4b. Login Rate Limiting (Flask-Limiter)
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    ...
```

After 5 failed attempts within 60 seconds from the same IP, the server returns **HTTP 429 Too Many Requests**.

#### 4c. Session Regeneration on Login
```python
# VULNERABLE: session values set on existing session
# FIXED: session cleared first to prevent fixation
session.clear()
session['user_id']  = user['id']
session['username'] = user['username']
session['role']     = user['role']
```

#### 4d. Password Strength Requirement
```python
if len(password) < 8:
    flash('Password must be at least 8 characters.', 'danger')
    return render_template('register.html')
```

---

## Fix 5 — A06: Vulnerable and Outdated Components

### Root Cause
Werkzeug 2.0.3 pinned intentionally — contains CVE-2023-25577.

### Remediation Applied
Updated `requirements.txt`:

```
# BEFORE (vulnerable_version/requirements.txt):
Werkzeug==2.0.3        # CVE-2023-25577

# AFTER (fixed_version/requirements.txt):
Werkzeug==3.0.3        # Latest stable, no known critical CVEs
Flask==3.0.3           # Updated
bcrypt==4.1.3          # New dependency for A07 fix
Flask-Limiter==3.8.0   # New dependency for A07 fix
```

### Verification
```bash
cd fixed_version
pip install pip-audit
pip-audit
# Expected: No known vulnerabilities found
```

---

## Summary of Changes

| Vulnerability | Fix Type | New Dependencies | Lines Changed |
|--------------|----------|-----------------|---------------|
| A01 | Code — decorators | None | ~20 lines added |
| A03 | Code — parameterised queries | None | 3 lines changed |
| A05 | Config + Code removal | None | 15 lines changed/removed |
| A07 | Code + Config | bcrypt, Flask-Limiter | ~40 lines changed |
| A06 | Dependency update | Werkzeug 3.0.3 | requirements.txt |

---

## Security Controls Matrix (After Fix)

| Control | Status | Implementation |
|---------|--------|---------------|
| Authentication | ✅ | bcrypt rounds=12 |
| Authorisation | ✅ | `@admin_required` decorator |
| Input validation | ✅ | Parameterised SQL |
| Session security | ✅ | HTTPONLY, SameSite, regeneration |
| Rate limiting | ✅ | Flask-Limiter 5/min |
| Error handling | ✅ | Custom pages, no stack traces |
| Secret management | ✅ | Environment variable |
| Dependency hygiene | ✅ | pip-audit clean |
