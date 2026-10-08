"""
init_db.py — Generate fresh bcrypt hashes and initialise the fixed database.
Run this ONCE before starting the fixed version for the first time.

Usage:
    cd fixed_version
    python init_db.py
"""

import sqlite3
import bcrypt
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'secureshop_fixed.db')

SEED_USERS = [
    ('admin', 'admin@secureshop.local', 'Admin@Secure2026', 'admin'),
    ('alice', 'alice@example.local',    'Alice@2026',        'user'),
    ('bob',   'bob@example.local',      'Bob@secure9',       'user'),
]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def init_db():
    # Remove existing DB so we start clean
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"[+] Removed existing database: {DATABASE}")

    conn = sqlite3.connect(DATABASE)
    cur  = conn.cursor()

    # Schema
    cur.executescript("""
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # Seed users with fresh bcrypt hashes
    print("[+] Creating users with bcrypt hashes...")
    for username, email, password, role in SEED_USERS:
        h = hash_password(password)
        cur.execute(
            "INSERT OR IGNORE INTO users (username, email, password, role) VALUES (?,?,?,?)",
            (username, email, h, role)
        )
        print(f"    {username:10s} / {password:20s}  →  {h[:30]}...")

    # Seed products
    products = [
        ('Wireless Noise-Cancelling Headphones',
         'Premium over-ear headphones with 30-hour battery life and active noise cancellation.',
         149.99, 50, 'Electronics', '/static/images/headphones.png'),
        ('Mechanical Gaming Keyboard',
         'RGB backlit mechanical keyboard with Cherry MX switches for lightning-fast response.',
         89.99, 35, 'Electronics', '/static/images/keyboard.png'),
        ('Ultra-Wide Gaming Monitor',
         '34-inch curved ultra-wide monitor with 144Hz refresh rate and 1ms response time.',
         499.99, 15, 'Electronics', '/static/images/monitor.png'),
        ('Ergonomic Office Chair',
         'Fully adjustable lumbar support chair designed for 8+ hours of comfortable use.',
         299.99, 20, 'Furniture', '/static/images/chair.png'),
        ('USB-C Hub 7-in-1',
         'Expand your laptop with HDMI 4K, 3x USB-A, SD card, USB-C PD 100W, and Ethernet.',
         49.99, 100, 'Accessories', '/static/images/hub.png'),
        ('Portable SSD 1TB',
         'Blazing fast 1050MB/s read/write, pocket-sized, shock-resistant portable SSD.',
         109.99, 60, 'Storage', '/static/images/ssd.png'),
        ('Smart LED Desk Lamp',
         'Touch-controlled LED lamp with wireless Qi charging base and 5 color temperatures.',
         59.99, 45, 'Accessories', '/static/images/lamp.png'),
        ('4K Webcam with Mic',
         'Crystal-clear 4K streaming webcam with built-in stereo microphone and auto-focus.',
         79.99, 30, 'Electronics', '/static/images/webcam.png'),
        ('Standing Desk Converter',
         'Transform any desk into a sit-stand workstation in seconds. Supports up to 35 lbs.',
         199.99, 25, 'Furniture', '/static/images/desk.png'),
        ('Wireless Charging Pad',
         '15W fast wireless charger compatible with Qi devices. Ultra-slim profile.',
         29.99, 80, 'Accessories', '/static/images/charger.png'),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO products (name, description, price, stock, category, image_url) VALUES (?,?,?,?,?,?)",
        products
    )
    print(f"[+] Inserted {len(products)} products.")

    cur.executemany(
        "INSERT OR IGNORE INTO orders (user_id, total, status, created_at) VALUES (?,?,?,?)",
        [
            (2, 239.98, 'confirmed', '2026-09-15 10:30:00'),
            (2, 499.99, 'shipped',   '2026-09-20 14:15:00'),
            (3, 149.99, 'confirmed', '2026-09-25 09:45:00'),
        ]
    )
    print("[+] Inserted 3 sample orders.")

    conn.commit()
    conn.close()
    print(f"\n✅ Database ready: {DATABASE}")
    print("\nLogin credentials (FIXED VERSION):")
    print("  Admin : admin / Admin@Secure2026")
    print("  User  : alice / Alice@2026")
    print("  User  : bob   / Bob@secure9")

if __name__ == '__main__':
    init_db()
