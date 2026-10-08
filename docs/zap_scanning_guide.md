# OWASP ZAP Scanning Guide
## SecureShop — Step-by-Step Automated Scanning

> This guide walks you through running OWASP ZAP against both versions of SecureShop and interpreting the results.

---

## Prerequisites

1. **OWASP ZAP** installed — download from https://zaproxy.org/download/
2. SecureShop vulnerable version running on `http://localhost:5000`
3. A web browser (Chrome or Firefox recommended)
4. Both Flask apps running in separate terminals

---

## Part 1 — Scan the VULNERABLE Version

### Step 1: Start the Vulnerable App
```bash
cd SecureShop/vulnerable_version
venv\Scripts\activate
python app.py
# → Running on http://0.0.0.0:5000
```

### Step 2: Open OWASP ZAP
- Launch ZAP from your applications menu
- Choose **"Automated Scan"** from the Welcome Screen (or use Manual Explore)

### Step 3: Configure Browser Proxy (for Manual Explore)
If using Manual Explore mode:
1. In ZAP: Tools → Options → Local Proxies → Default: `localhost:8080`
2. In your browser: Settings → Proxy → Manual → `localhost:8080`
3. Browse the app while ZAP records requests

### Step 4: Automated Scan (Recommended for Assignment)
1. In ZAP: Click **"Automated Scan"**
2. Set **URL to attack:** `http://localhost:5000`
3. Check **"Use standard spider"**
4. Check **"Use Ajax spider"** (for better coverage)
5. Click **"Attack"**
6. Wait for the scan to complete (5–15 minutes)

### Step 5: Authenticated Scan (Important — catches A01)
To scan authenticated pages:
1. Go to: **Tools → Options → HTTP Sessions**
2. First, log in to the app via ZAP's browser: `http://localhost:5000/login`
3. In ZAP History tab — right-click the POST /login request → **"Flag as Context: Include in Context"**
4. Set up Form-Based Authentication with username/password fields
5. Re-run the Spider with this context

Alternatively:
1. **Manually explore** all pages while ZAP proxy is active
2. Then click: **Active Scan → Right-click site → Active Scan**

### Step 6: Export the Report
1. ZAP Menu: **Report → Generate Report**
2. Choose format: **HTML** (best for submission)
3. Save as: `evidence/zap_scan_vulnerable.html`
4. Also export XML if required: `evidence/zap_scan_vulnerable.xml`

### Expected Findings on Vulnerable Version
| Alert | Risk Level | Related Vulnerability |
|-------|-----------|----------------------|
| SQL Injection | High | A03 |
| Information Disclosure – Debug Errors | Medium | A05 |
| Application Error Disclosure | Medium | A05 |
| Cookie Without Secure Flag | Low | A07 |
| Cookie Without HttpOnly Flag | Low | A07 |
| Missing Anti-clickjacking Header | Medium | A05 |
| Server Leaks Version Information | Low | A05 |
| Content Security Policy Header Missing | Medium | A05 |

> **Note:** ZAP may not catch Broken Access Control (A01) automatically — this requires manual verification. Document your manual test: login as regular user, navigate to `/admin`, observe no 403 is returned.

---

## Part 2 — Scan the FIXED Version

### Step 1: Start the Fixed App
```bash
cd SecureShop/fixed_version
venv\Scripts\activate
python init_db.py    # first time only
python app.py
# → Running on http://127.0.0.1:5001
```

### Step 2: Configure ZAP for Port 5001
1. In ZAP: Automated Scan → URL: `http://localhost:5001`
2. Run the same scan configuration as Part 1

### Step 3: Test Rate Limiting (A07 Fix)
1. In ZAP: Tools → Options → Break Points
2. Or use: **Fuzzer** on POST `/login` with rapid requests
3. After 5 requests/minute: expect **HTTP 429** response

### Step 4: Test Access Control (A01 Fix — Manual)
1. In ZAP browser: login as `alice` / `Alice@2026`
2. Navigate to `http://localhost:5001/admin`
3. Observe: **HTTP 403 Forbidden** returned
4. Screenshot this response

### Step 5: Export Fixed Version Report
- Save as: `evidence/zap_scan_fixed.html`

### Expected Findings on Fixed Version
- SQL Injection: **Not found** (parameterised queries)
- Debug endpoints: **Not found** (removed)
- Access Control: **Fixed** (manual verification shows 403)
- Most alerts reduced to **Informational** or removed entirely

---

## Part 3 — Manual Verification Tests

### Test A03 — SQL Injection (Manual)
```bash
# Vulnerable version — should return user data
curl "http://localhost:5000/search?q=%27+UNION+SELECT+id%2Cusername%2Cpassword%2Cemail%2Crole%2Ccreated_at+FROM+users--"

# Fixed version — should return empty / safe response
curl "http://localhost:5001/search?q=%27+UNION+SELECT+id%2Cusername%2Cpassword%2Cemail%2Crole%2Ccreated_at+FROM+users--"
```

### Test A05 — Config Exposure (Manual)
```bash
# Vulnerable — should return JSON with secret key
curl http://localhost:5000/debug/config

# Fixed — should return 404
curl http://localhost:5001/debug/config
```

### Test A07 — Rate Limiting (Manual)
```bash
# Send 6 rapid login attempts to fixed version — expect 429 on 6th
for i in {1..6}; do
    curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:5001/login \
    -d "username=alice&password=wrong"
done
```

### Test A01 — Broken Access Control (Manual)
```
Vulnerable: Login as alice → GET /admin → 200 OK (FAIL)
Fixed:      Login as alice → GET /admin → 403 Forbidden (PASS)
```

---

## ZAP Tips for Better Coverage

1. **Increase Spider depth:** ZAP Options → Spider → Max Depth: 10
2. **Enable passive scanning:** Always on by default
3. **Add session tokens:** Helps ZAP understand authenticated state
4. **Use AJAX Spider** for JavaScript-heavy pages
5. **Review all findings** — not just High/Medium; Low alerts also demonstrate issues

---

## ZAP Report Interpretation

| Alert Level | Meaning | Action |
|------------|---------|--------|
| 🔴 High | Likely exploitable | Must fix before production |
| 🟡 Medium | Potentially exploitable | Fix in next sprint |
| 🔵 Low | Minor issue | Fix when possible |
| ℹ️ Informational | Not a vulnerability | Note and review |

---

## Screenshot Checklist for ZAP Evidence

- [ ] ZAP main window showing alerts on vulnerable version
- [ ] ZAP alert detail for SQL Injection finding
- [ ] ZAP alert detail for information disclosure
- [ ] ZAP scan progress bar (active scan running)
- [ ] ZAP HTML report summary page (vulnerable)
- [ ] ZAP HTML report summary page (fixed) — fewer alerts
- [ ] Browser showing 429 rate limit response (fixed)
- [ ] Browser showing 403 on `/admin` (fixed)
