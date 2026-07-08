import sqlite3
import os

DB_PATH = "uploads/database.db"

def init_db():
    os.makedirs("uploads", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        
        # Create tables
        c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS materials (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category_id INTEGER, file_id TEXT, file_type TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')

        # Default Support Settings
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('support_username', '@admin')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('support_link', 'https://t.me/admin')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('contact_text', 'For any issues, please contact support.')")

        # Default Categories (Courses, Hacks)
        c.execute("SELECT COUNT(*) FROM categories")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO categories (name) VALUES ('📚 Courses'), ('💻 Hacks')")
        
        conn.commit()

def execute_query(query, params=(), fetch=False, fetch_all=False):
    """Executes a query safely and returns results if required."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query, params)
        if fetch:
            row = c.fetchone()
            return dict(row) if row else None
        if fetch_all:
            return [dict(row) for row in c.fetchall()]
        conn.commit()
        return c.lastrowid