"""database.py - connection handling and table creation (SQLite).

SQLite is built into Python (the sqlite3 module), so nothing extra needs
to be installed. The whole database lives in one file: data/inventory.db
"""

import os
import sqlite3
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "inventory.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name     TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'staff' CHECK (role IN ('admin', 'staff')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS products (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    category   TEXT NOT NULL COLLATE NOCASE,
    quantity   INTEGER NOT NULL CHECK (quantity >= 0),
    price      REAL NOT NULL CHECK (price >= 0),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
"""


@contextmanager
def get_connection(db_path=None):
    """Open a database connection, and always close it afterwards.

    Usage:
        with get_connection() as conn:
            conn.execute(...)

    - If the block finishes normally, changes are saved (commit).
    - If an error happens, changes are undone (rollback).
    """
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row          # lets us read columns by name: row["price"]
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite needs this switched on every time
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None):
    """Create the tables if they do not exist yet. Safe to call every start-up."""
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
