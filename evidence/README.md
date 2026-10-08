# Evidence & Screenshots Required
## SecureShop Security Lab

This folder contains all evidence collected during the security assessment.

---

## 📸 Required Screenshots

Place screenshots in this folder with the exact filenames listed below.

### Phase 1 — Application Running (Vulnerable Version)

| Filename | What to Capture |
|----------|----------------|
| `01_vuln_homepage.png` | SecureShop vulnerable version home page at localhost:5000 |
| `02_vuln_login_page.png` | Login page with demo credentials visible |
| `03_vuln_products.png` | Product listing / search page |
| `04_vuln_admin_as_user.png` | Admin dashboard accessed while logged in as `alice` (A01) |

### Phase 2 — SQL Injection Evidence (A03)

| Filename | What to Capture |
|----------|----------------|
| `05_sqli_basic_payload.png` | Search box with `' OR '1'='1` returning all products |
| `06_sqli_union_payload.png` | UNION SELECT returning user table data in product listing |
| `07_sqli_error.png` | Database error message exposed to user (A05 too) |

### Phase 3 — Security Misconfiguration (A05)

| Filename | What to Capture |
|----------|----------------|
| `08_debug_config_endpoint.png` | `http://localhost:5000/debug/config` showing secret key + env vars |
| `09_debug_error_page.png` | Werkzeug debug traceback shown on error (DEBUG=True) |

### Phase 4 — OWASP ZAP Scan (Vulnerable Version)

| Filename | What to Capture |
|----------|----------------|
| `10_zap_scan_setup.png` | ZAP configured and scanning localhost:5000 |
| `11_zap_spider_results.png` | Spider results showing discovered URLs |
| `12_zap_active_scan.png` | Active scan progress bar running |
| `13_zap_alerts_summary.png` | ZAP Alerts tab showing High/Medium findings |
| `14_zap_sqli_alert.png` | SQL Injection alert detail in ZAP |
| `15_zap_report_vulnerable.png` | ZAP HTML report summary for vulnerable version |

### Phase 5 — Fixed Version Verification (Retest)

| Filename | What to Capture |
|----------|----------------|
| `16_fixed_homepage.png` | Fixed version home page at localhost:5001 |
| `17_retest_a01_403.png` | HTTP 403 page when alice tries to access /admin |
| `18_retest_a03_safe.png` | SQL injection payload in fixed version — 0 results, no error |
| `19_retest_a05_404.png` | 404 returned for /debug/config on fixed version |
| `20_retest_a07_429.png` | 429 Too Many Requests after 5 login attempts |
| `21_zap_report_fixed.png` | ZAP HTML report summary for fixed version (fewer alerts) |

### Phase 6 — Before/After Comparison

| Filename | What to Capture |
|----------|----------------|
| `22_pip_audit_vulnerable.png` | pip-audit output on vulnerable version showing CVE |
| `23_pip_audit_fixed.png` | pip-audit output on fixed version — "No vulnerabilities found" |

---

## 📄 Files to Save (non-screenshots)

| Filename | How to Get It |
|----------|--------------|
| `zap_scan_vulnerable.html` | ZAP → Report → Generate Report (HTML) for vulnerable version |
| `zap_scan_fixed.html` | ZAP → Report → Generate Report (HTML) for fixed version |
| `zap_scan_vulnerable.xml` | ZAP → Report → Generate Report (XML) for vulnerable version |

---

## 📝 Tips for Good Screenshots

1. **Show the URL bar** — it proves which page/endpoint you're on
2. **Show the full page** — not just the interesting part
3. **For terminal output** — capture the entire terminal window
4. **Resolution** — use at least 1200px wide screenshots
5. **Annotations** — optionally add red arrows/boxes to highlight key findings

---

## 🗂️ After Collecting Evidence

1. Add screenshots to this `evidence/` folder
2. Update `docs/retest_report.md` with actual ZAP counts
3. Commit to GitHub:

```bash
git add evidence/
git commit -m "Add security lab evidence and ZAP scan results"
git push
```
