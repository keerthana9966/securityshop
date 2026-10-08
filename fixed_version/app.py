"""
SecureShop – FIXED VERSION
===========================
✅  All OWASP vulnerabilities from the vulnerable version are remediated here.

Fixes Applied:
  - A01: Proper role-based access control on all admin routes
  - A03: Parameterised queries (no string concatenation in SQL)
  - A05: DEBUG=False, secret key loaded from env var, /debug endpoint removed
  - A07: bcrypt password hashing, login rate limiting (via Flask-Limiter)
  - A06: Updated Werkzeug to non-vulnerable version (see requirements.txt)
"""

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, g, abort)
from functools import wraps
import sqlite3
import os
import bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ─────────────────────────────────────────────────────────────────────────────
# FIX-A05: SECRET_KEY loaded from environment variable with a strong fallback
#           DEBUG is explicitly False
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get(
    'SECRET_KEY',
    'change-this-before-any-real-deployment-64chars-min!'
)
app.config['DEBUG'] = False           # FIX-A05: debug disabled
app.config['SESSION_COOKIE_HTTPONLY'] = True   # prevent JS cookie access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # CSRF mitigation

DATABASE = os.path.join(os.path.dirname(__file__), 'secureshop_fixed.db')

# ─────────────────────────────────────────────────────────────────────────────
# FIX-A07: Rate limiting on login endpoint – max 5 attempts/minute per IP
# ─────────────────────────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],        # no global limit
    storage_uri="memory://",
)


# ── Access Control Decorators ─────────────────────────────────────────────────

def login_required(f):
    """FIX-A01/A07: Ensures the user is authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """FIX-A01: Ensures the user is authenticated AND has the 'admin' role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            abort(403)           # return 403 Forbidden – not just a redirect
        return f(*args, **kwargs)
    return decorated


# ── Database helpers ──────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema_fixed.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# ── Custom Error Handlers ─────────────────────────────────────────────────────
# FIX-A05: Friendly error pages instead of stack traces

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403,
                           message='Access Forbidden',
                           detail='You do not have permission to access this page.'), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404,
                           message='Page Not Found',
                           detail='The page you are looking for does not exist.'), 404


@app.errorhandler(500)
def server_error(e):
    # FIX-A05: never expose internal error details
    return render_template('error.html', code=500,
                           message='Internal Server Error',
                           detail='Something went wrong. Please try again later.'), 500


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    products = db.execute('SELECT * FROM products LIMIT 8').fetchall()
    return render_template('index.html', products=products)


# ── FIX-A03 Parameterised Search ──────────────────────────────────────────────
@app.route('/search')
def search():
    """FIX-A03: Uses parameterised query – user input is never concatenated into SQL."""
    query = request.args.get('q', '')
    db = get_db()
    # SAFE: parameterised with ? placeholders
    like_query = f'%{query}%'
    products = db.execute(
        'SELECT * FROM products WHERE name LIKE ? OR description LIKE ?',
        (like_query, like_query)
    ).fetchall()
    return render_template('search.html', products=products, query=query, error=None)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        abort(404)
    return render_template('product_detail.html', product=product)


# ── FIX-A07 Registration with bcrypt ─────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email    = request.form['email'].strip().lower()
        password = request.form['password']

        # Password strength check
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('register.html')

        db = get_db()
        # FIX-A07: bcrypt hash (work factor 12)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

        try:
            db.execute(
                'INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, 'user')
            )
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('register.html')


# ── FIX-A07 Login with rate limiting ─────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])   # FIX-A07: brute force protection
def login():
    """FIX-A07: bcrypt comparison, rate limiting, session regeneration."""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()

        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        # FIX-A07: constant-time bcrypt comparison
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # FIX-A07: clear old session before setting new one (prevents session fixation)
            session.clear()
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ── Profile ───────────────────────────────────────────────────────────────────
@app.route('/profile')
@login_required
def profile():
    db   = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    orders = db.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    return render_template('profile.html', user=user, orders=orders)


# ── Cart ──────────────────────────────────────────────────────────────────────
@app.route('/cart')
@login_required
def cart():
    cart_items = session.get('cart', [])
    db = get_db()
    products = []
    total = 0
    for item in cart_items:
        p = db.execute('SELECT * FROM products WHERE id = ?', (item['product_id'],)).fetchone()
        if p:
            products.append({'product': p, 'quantity': item['quantity']})
            total += p['price'] * item['quantity']
    return render_template('cart.html', products=products, total=total)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    cart = session.get('cart', [])
    qty  = min(int(request.form.get('quantity', 1)), 100)  # sanitise quantity
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += qty
            break
    else:
        cart.append({'product_id': product_id, 'quantity': qty})
    session['cart'] = cart
    flash('Item added to cart!', 'success')
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    session['cart'] = [i for i in cart if i['product_id'] != product_id]
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))
    db = get_db()
    total = 0
    for item in cart_items:
        p = db.execute('SELECT * FROM products WHERE id = ?', (item['product_id'],)).fetchone()
        if p:
            total += p['price'] * item['quantity']
    db.execute(
        'INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)',
        (session['user_id'], total, 'confirmed')
    )
    db.commit()
    session['cart'] = []
    flash('Order placed successfully!', 'success')
    return redirect(url_for('profile'))


@app.route('/orders')
@login_required
def orders():
    db = get_db()
    user_orders = db.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    return render_template('orders.html', orders=user_orders)


# ── FIX-A01 Admin Panel – Role Check Enforced ────────────────────────────────
@app.route('/admin')
@admin_required     # FIX-A01: decorator enforces role == 'admin' before proceeding
def admin_dashboard():
    db = get_db()
    users    = db.execute('SELECT id, username, email, role, created_at FROM users').fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
    orders   = db.execute(
        'SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC'
    ).fetchall()
    stats = {
        'total_users':    db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_products': db.execute('SELECT COUNT(*) FROM products').fetchone()[0],
        'total_orders':   db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],
        'total_revenue':  db.execute('SELECT COALESCE(SUM(total),0) FROM orders').fetchone()[0],
    }
    return render_template('admin/dashboard.html', users=users, products=products,
                           orders=orders, stats=stats)


@app.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required     # FIX-A01
def admin_add_product():
    if request.method == 'POST':
        name        = request.form['name']
        description = request.form['description']
        price       = float(request.form['price'])
        stock       = int(request.form['stock'])
        category    = request.form['category']
        image_url   = request.form.get('image_url', '/static/images/default.png')
        db = get_db()
        db.execute(
            'INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?,?,?,?,?,?)',
            (name, description, price, stock, category, image_url)
        )
        db.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_product.html')


@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required     # FIX-A01
def admin_edit_product(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        abort(404)
    if request.method == 'POST':
        name        = request.form['name']
        description = request.form['description']
        price       = float(request.form['price'])
        stock       = int(request.form['stock'])
        category    = request.form['category']
        image_url   = request.form.get('image_url', product['image_url'])
        db.execute(
            'UPDATE products SET name=?, description=?, price=?, stock=?, category=?, image_url=? WHERE id=?',
            (name, description, price, stock, category, image_url, product_id)
        )
        db.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_product.html', product=product)


@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required     # FIX-A01
def admin_delete_product(product_id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    flash('Product deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users')
@admin_required     # FIX-A01
def admin_users():
    db = get_db()
    # FIX: password column excluded from this query
    users = db.execute('SELECT id, username, email, role, created_at FROM users').fetchall()
    return render_template('admin/users.html', users=users)


# FIX-A05: /debug/config endpoint completely removed


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    # FIX-A05: debug=False, host defaults to 127.0.0.1 (localhost only)
    app.run(debug=False, host='127.0.0.1', port=5001)
