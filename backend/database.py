"""SQLite database session and base setup using only the stdlib sqlite3 module.

We deliberately avoid SQLAlchemy so the app has zero hard database dependencies
beyond Python itself. All queries are parameterized to prevent SQL injection.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import settings

DB_PATH = settings.database_url.replace("sqlite:///", "").replace("sqlite://", "")


def _resolve_path() -> Path:
    p = Path(DB_PATH)
    if not p.is_absolute():
        # Resolve relative to this file's parent (backend/)
        p = Path(__file__).resolve().parent / p
    return p


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_resolve_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    """Yield a connection inside a transaction; commit/rollback/close cleanly."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and seed an admin user if one does not exist."""
    with db_session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                hashed_password TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                lat REAL,
                lng REAL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (author_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                lat REAL,
                lng REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
            CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);
            CREATE INDEX IF NOT EXISTS idx_checkins_user ON checkins(user_id);
            """
        )

        # Seed admin user if none exists.
        cur = conn.execute("SELECT COUNT(*) AS c FROM users")
        if cur.fetchone()["c"] == 0:
            from security import hash_password

            conn.execute(
                """
                INSERT INTO users
                    (username, phone, display_name, hashed_password, is_admin, created_at)
                VALUES (?, ?, ?, ?, 1, datetime('now'))
                """,
                (
                    settings.seed_admin_username,
                    settings.seed_admin_phone,
                    "Salama Admin",
                    hash_password(settings.seed_admin_password),
                ),
            )
