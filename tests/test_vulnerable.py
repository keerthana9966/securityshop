"""
tests/test_vulnerable.py
Tests that demonstrate the vulnerabilities ARE present in the vulnerable version.
Run from SecureShop root: pytest tests/test_vulnerable.py -v
"""
import sys
import os
import pytest

# Add vulnerable_version to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vulnerable_version'))

import app as vuln_app


@pytest.fixture
def client(tmp_path):
    """Create a test client with a temp database."""
    db_path = str(tmp_path / 'test_vuln.db')
    vuln_app.app.config['TESTING'] = True
    vuln_app.app.config['SECRET_KEY'] = 'testsecret'
    vuln_app.DATABASE = db_path

    with vuln_app.app.app_context():
        vuln_app.init_db()

    with vuln_app.app.test_client() as client:
        yield client


# ── Helper ───────────────────────────────────────────────────────────────────

def login(client, username, password):
    import hashlib
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestVulnerableVersion:

    def test_home_page_loads(self, client):
        """Home page should return 200."""
        resp = client.get('/')
        assert resp.status_code == 200

    def test_register_and_login(self, client):
        """Users can register and log in."""
        client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        resp = login(client, 'testuser', 'password123')
        assert resp.status_code == 200

    def test_search_returns_products(self, client):
        """Search with empty query returns products."""
        resp = client.get('/search?q=')
        assert resp.status_code == 200

    def test_a01_regular_user_can_access_admin(self, client):
        """
        VULNERABILITY A01: Any logged-in user can access /admin.
        This test PASSES on the vulnerable version (no 403 returned).
        """
        # Register a regular user
        client.post('/register', data={
            'username': 'regularuser',
            'email': 'regular@example.com',
            'password': 'password123'
        })
        login(client, 'regularuser', 'password123')

        # Regular user accesses admin panel — should be 200 (VULNERABLE)
        resp = client.get('/admin')
        assert resp.status_code == 200, (
            "VULN-A01: Regular user accessed /admin without role check"
        )

    def test_a03_sql_injection_search(self, client):
        """
        VULNERABILITY A03: SQL injection in search returns all rows.
        The payload ' OR '1'='1 bypasses the WHERE clause.
        """
        resp = client.get("/search?q=' OR '1'='1")
        assert resp.status_code == 200
        # The page loads (doesn't crash) — in real test you'd check for leaked data
        # This test just confirms the endpoint accepts the payload without error

    def test_a05_debug_config_exposed(self, client):
        """
        VULNERABILITY A05: /debug/config endpoint exposes secret key.
        No authentication required.
        """
        resp = client.get('/debug/config')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None, "Expected JSON response"
        assert 'secret_key' in data, "VULN-A05: Secret key exposed in /debug/config"

    def test_a07_md5_password_hashing(self, client):
        """
        VULNERABILITY A07: Passwords are stored as MD5 hashes.
        Verify by checking the hash matches MD5 of password.
        """
        import hashlib
        with vuln_app.app.app_context():
            db = vuln_app.get_db()
            user = db.execute("SELECT password FROM users WHERE username='admin'").fetchone()
            if user:
                # Admin password in seed data is "admin123" → MD5
                expected_md5 = hashlib.md5(b'admin123').hexdigest()
                assert user['password'] == expected_md5, (
                    f"VULN-A07: Password stored as MD5: {user['password']}"
                )

    def test_a05_debug_mode_enabled(self):
        """
        VULNERABILITY A05: DEBUG mode is True in the vulnerable version.
        """
        assert vuln_app.app.config.get('DEBUG') is True, "VULN-A05: DEBUG should be True"

    def test_a05_weak_secret_key(self):
        """
        VULNERABILITY A05: Secret key is a weak hardcoded string.
        """
        # After test client init, the original key in source is "secret123"
        # We check the source code directly
        source_path = os.path.join(
            os.path.dirname(__file__), '..', 'vulnerable_version', 'app.py'
        )
        with open(source_path) as f:
            source = f.read()
        assert '"secret123"' in source or "'secret123'" in source, (
            "VULN-A05: Weak hardcoded secret key present in source"
        )

    def test_product_detail_page(self, client):
        """Product detail page loads for existing product."""
        resp = client.get('/product/1')
        assert resp.status_code == 200

    def test_404_for_missing_product(self, client):
        """Non-existent product returns 404."""
        resp = client.get('/product/99999')
        assert resp.status_code == 404
