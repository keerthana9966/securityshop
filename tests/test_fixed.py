"""
tests/test_fixed.py
Tests that verify all vulnerabilities are FIXED in the fixed version.
Run from SecureShop root: pytest tests/test_fixed.py -v
"""
import sys
import os
import pytest

# Add fixed_version to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fixed_version'))

import app as fixed_app


@pytest.fixture
def client(tmp_path):
    """Create a test client with a temp database."""
    db_path = str(tmp_path / 'test_fixed.db')
    fixed_app.app.config['TESTING'] = True
    fixed_app.app.config['SECRET_KEY'] = 'test-secure-key-for-testing-only-12345678'
    fixed_app.DATABASE = db_path

    with fixed_app.app.app_context():
        # Manually create tables and seed data
        db = fixed_app.get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0,
                category TEXT,
                image_url TEXT DEFAULT '/static/images/default.png',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        import bcrypt
        # Seed admin
        admin_hash = bcrypt.hashpw(b'Admin@Secure2026', bcrypt.gensalt(rounds=4)).decode()
        user_hash  = bcrypt.hashpw(b'Alice@2026',       bcrypt.gensalt(rounds=4)).decode()
        db.execute("INSERT OR IGNORE INTO users (username,email,password,role) VALUES (?,?,?,?)",
                   ('admin', 'admin@test.local', admin_hash, 'admin'))
        db.execute("INSERT OR IGNORE INTO users (username,email,password,role) VALUES (?,?,?,?)",
                   ('alice', 'alice@test.local', user_hash, 'user'))
        db.execute("INSERT OR IGNORE INTO products (name,description,price,stock,category) VALUES (?,?,?,?,?)",
                   ('Test Product', 'A test product description', 29.99, 10, 'Electronics'))
        db.commit()

    with fixed_app.app.test_client() as client:
        yield client


# ── Helpers ───────────────────────────────────────────────────────────────────

def login_user(client, username, password):
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def login_admin(client):
    return login_user(client, 'admin', 'Admin@Secure2026')


def login_regular(client):
    return login_user(client, 'alice', 'Alice@2026')


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestFixedVersion:

    def test_home_page_loads(self, client):
        """Home page should return 200."""
        resp = client.get('/')
        assert resp.status_code == 200

    def test_register_requires_min_password(self, client):
        """FIX-A07: Registration rejects passwords shorter than 8 chars."""
        resp = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'short'   # only 5 chars
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Password must be at least 8' in resp.data

    def test_login_with_correct_credentials(self, client):
        """FIX-A07: Login works with correct bcrypt password."""
        resp = login_user(client, 'alice', 'Alice@2026')
        assert resp.status_code == 200

    def test_login_with_wrong_credentials(self, client):
        """FIX-A07: Login fails with wrong password."""
        resp = login_user(client, 'alice', 'wrongpassword')
        assert b'Invalid credentials' in resp.data

    def test_a01_fix_regular_user_cannot_access_admin(self, client):
        """
        FIX-A01: Regular user is returned 403 when accessing /admin.
        """
        login_regular(client)
        resp = client.get('/admin')
        assert resp.status_code == 403, (
            f"FIX-A01 FAILED: Expected 403 but got {resp.status_code}. "
            "Admin panel is still accessible to regular users!"
        )

    def test_a01_fix_admin_can_access_admin(self, client):
        """
        FIX-A01: Admin user CAN access /admin.
        """
        login_admin(client)
        resp = client.get('/admin')
        assert resp.status_code == 200, (
            f"Admin user should access /admin but got {resp.status_code}"
        )

    def test_a01_fix_unauthenticated_redirected_from_admin(self, client):
        """
        FIX-A01: Unauthenticated access to /admin redirects to login.
        """
        resp = client.get('/admin')
        # Should redirect (302) to login
        assert resp.status_code in (302, 308)

    def test_a03_fix_sql_injection_in_search(self, client):
        """
        FIX-A03: SQL injection payloads do not cause errors or leak data.
        """
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE products; --",
            "' UNION SELECT id,username,password,email,role,created_at FROM users--",
        ]
        for payload in payloads:
            resp = client.get(f'/search?q={payload}')
            assert resp.status_code == 200, f"Search crashed on payload: {payload}"
            # Should not expose user data
            assert b'admin@' not in resp.data, f"User data leaked by payload: {payload}"
            assert b'password' not in resp.data.lower() or b'Enter password' in resp.data, \
                f"Password data may be leaked by payload: {payload}"

    def test_a05_fix_debug_config_endpoint_removed(self, client):
        """
        FIX-A05: /debug/config endpoint no longer exists.
        """
        resp = client.get('/debug/config')
        assert resp.status_code == 404, (
            f"FIX-A05 FAILED: /debug/config returned {resp.status_code} "
            "but should return 404. Endpoint still exists!"
        )

    def test_a05_fix_debug_mode_disabled(self):
        """
        FIX-A05: DEBUG mode is False in the fixed version.
        """
        assert fixed_app.app.config.get('DEBUG') is False, (
            "FIX-A05 FAILED: DEBUG should be False"
        )

    def test_a07_fix_passwords_use_bcrypt(self, client):
        """
        FIX-A07: Passwords are stored as bcrypt hashes (start with $2b$).
        """
        import bcrypt
        with fixed_app.app.app_context():
            db = fixed_app.get_db()
            user = db.execute("SELECT password FROM users WHERE username='admin'").fetchone()
            if user:
                pw_hash = user['password']
                assert pw_hash.startswith('$2b$'), (
                    f"FIX-A07 FAILED: Password not using bcrypt format: {pw_hash[:20]}..."
                )
                # Verify bcrypt check works
                assert bcrypt.checkpw(b'Admin@Secure2026', pw_hash.encode()), (
                    "FIX-A07 FAILED: bcrypt verification failed for admin password"
                )

    def test_profile_requires_login(self, client):
        """FIX: /profile redirects unauthenticated users to login."""
        resp = client.get('/profile')
        assert resp.status_code in (302, 308)

    def test_cart_requires_login(self, client):
        """FIX: /cart redirects unauthenticated users to login."""
        resp = client.get('/cart')
        assert resp.status_code in (302, 308)

    def test_product_detail_loads(self, client):
        """Product detail page loads for an existing product."""
        resp = client.get('/product/1')
        assert resp.status_code == 200

    def test_custom_404_page(self, client):
        """FIX-A05: 404 returns custom error page, not stack trace."""
        resp = client.get('/nonexistent-page-xyz')
        assert resp.status_code == 404
        # Should not contain Python traceback
        assert b'Traceback' not in resp.data
        assert b'File "' not in resp.data

    def test_admin_products_add_blocked_for_regular_user(self, client):
        """FIX-A01: Regular users cannot add products."""
        login_regular(client)
        resp = client.get('/admin/products/add')
        assert resp.status_code == 403

    def test_admin_users_blocked_for_regular_user(self, client):
        """FIX-A01: Regular users cannot list users."""
        login_regular(client)
        resp = client.get('/admin/users')
        assert resp.status_code == 403
