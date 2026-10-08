"""
SecureShop - VULNERABLE VERSION
================================
⚠️  EDUCATIONAL SECURITY LAB  ⚠️
This application is INTENTIONALLY VULNERABLE for educational purposes.
It demonstrates common OWASP Top 10 vulnerabilities in a controlled, local environment.
DO NOT deploy this application publicly. Use only on localhost for learning purposes.

Vulnerabilities Demonstrated:
  - A01: Broken Access Control  (admin panel accessible without proper role check)
  - A03: SQL Injection           (raw string formatting in queries)
  - A05: Security Misconfiguration (DEBUG=True, secret key exposed, verbose errors)
  - A07: Auth/Session Weakness   (weak session secret, no brute-force protection)
  - A06: Vulnerable Components   (intentionally outdated Werkzeug in requirements.txt)
"""

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, g, jsonify)
import sqlite3
import os
import hashlib

# ─────────────────────────────────────────────────────────────────────────────
# A05 – Security Misconfiguration: DEBUG=True exposes the interactive debugger
#        SECRET_KEY is hardcoded and weak – trivially guessable
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "secret123"          # VULN-A05: hardcoded weak secret key
app.config['DEBUG'] = True            # VULN-A05: debug mode enabled in production-like env

DATABASE = os.path.join(os.path.dirname(__file__), 'secureshop.db')


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
    """Initialise database with schema and seed data."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    products = db.execute('SELECT * FROM products LIMIT 8').fetchall()
    return render_template('index.html', products=products)


# ── A03 SQL Injection – Search ────────────────────────────────────────────────
@app.route('/search')
def search():
    """
    VULN-A03: User input is directly concatenated into the SQL query string.
    Try: ' OR '1'='1   or   '; DROP TABLE products; --
    """
    query = request.args.get('q', '')
    db = get_db()
    # VULNERABLE: raw string formatting
    sql = "SELECT * FROM products WHERE name LIKE '%" + query + "%' OR description LIKE '%" + query + "%'"
    try:
        products = db.execute(sql).fetchall()
    except Exception as e:
        # A05: full error exposed to user
        return render_template('search.html', products=[], query=query, error=str(e))
    return render_template('search.html', products=products, query=query, error=None)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        return render_template('404.html'), 404
    return render_template('product_detail.html', product=product)


# ── A07 Auth Weakness – Registration ──────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email    = request.form['email']
        password = request.form['password']
        db = get_db()

        # VULN-A07: MD5 (broken hash) instead of bcrypt / Argon2
        password_hash = hashlib.md5(password.encode()).hexdigest()

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


# ── A07 Auth Weakness – Login ─────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    VULN-A07: No rate limiting / brute-force protection.
              Session fixation possible – session not regenerated on login.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()

        # MD5 to match registration
        password_hash = hashlib.md5(password.encode()).hexdigest()

        user = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password_hash)
        ).fetchone()

        if user:
            # VULN-A07: session NOT cleared/regenerated → session fixation risk
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
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db  = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    orders = db.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    return render_template('profile.html', user=user, orders=orders)


# ── Cart ──────────────────────────────────────────────────────────────────────
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cart = session.get('cart', [])
    qty  = int(request.form.get('quantity', 1))
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
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    session['cart'] = [i for i in cart if i['product_id'] != product_id]
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
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


# ── Order History ─────────────────────────────────────────────────────────────
@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    user_orders = db.execute(
        'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    return render_template('orders.html', orders=user_orders)


# ── A01 Broken Access Control – Admin Panel ───────────────────────────────────
@app.route('/admin')
def admin_dashboard():
    """
    VULN-A01: No role verification performed.
              Any logged-in user can access /admin by navigating directly to the URL.
              Even unauthenticated users can access the page (only a soft redirect is done
              but role is never checked against the database).
    """
    # Only checks if logged in – does NOT verify role == 'admin'
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Missing:  if session.get('role') != 'admin': abort(403)
    db = get_db()
    users    = db.execute('SELECT id, username, email, role, created_at FROM users').fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
    orders   = db.execute('SELECT o.*, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC').fetchall()
    stats = {
        'total_users':    db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'total_products': db.execute('SELECT COUNT(*) FROM products').fetchone()[0],
        'total_orders':   db.execute('SELECT COUNT(*) FROM orders').fetchone()[0],
        'total_revenue':  db.execute('SELECT COALESCE(SUM(total),0) FROM orders').fetchone()[0],
    }
    return render_template('admin/dashboard.html', users=users, products=products,
                           orders=orders, stats=stats)


@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    # VULN-A01: again no role check
    if 'user_id' not in session:
        return redirect(url_for('login'))
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
def admin_edit_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
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
def admin_delete_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()
    flash('Product deleted.', 'warning')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users')
def admin_users():
    # VULN-A01: no role check
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    users = db.execute('SELECT * FROM users').fetchall()
    return render_template('admin/users.html', users=users)


# ── A05 – Exposed debug/info endpoint ─────────────────────────────────────────
@app.route('/debug/config')
def debug_config():
    """
    VULN-A05: Sensitive server configuration exposed via an unauthenticated endpoint.
    """
    return jsonify({
        'secret_key':   app.secret_key,
        'debug':        app.config.get('DEBUG'),
        'database':     DATABASE,
        'session_keys': list(session.keys()),
        'env_vars':     dict(os.environ),   # exposes all env vars!
    })


# ── Error handlers ────────────────────────────────────────────────────────────
# A05: no custom error pages – Flask default stack traces are shown in DEBUG mode

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    # VULN-A05: host='0.0.0.0' makes the debug server publicly accessible
    app.run(debug=True, host='0.0.0.0', port=5000)
