import sqlite3

DB_NAME = "database.db"

def get_db():
    """
    Returns a SQLite connection.
    Rows can be accessed as dictionaries.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database and creates tables if they don't exist.
    """
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        db.commit()
