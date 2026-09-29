"""users.py - registration, login and user management.

Every SQL statement uses ? placeholders. The values are passed separately
so the database treats them purely as data. This is what prevents
SQL injection.
"""

import re
import sqlite3

from database import get_connection
from security import hash_password, verify_password, check_password_strength

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def count_users(db_path=None):
    with get_connection(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def register_user(username, full_name, password, db_path=None):
    """Create an account. The very first account becomes the admin,
    every later account is a normal staff member. Returns (ok, message)."""
    username = username.strip()
    if not USERNAME_PATTERN.match(username):
        return False, "Username must be 3-20 characters: letters, numbers or underscore."
    ok, message = check_password_strength(password)
    if not ok:
        return False, message

    with get_connection(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        role = "admin" if total == 0 else "staff"
        try:
            conn.execute(
                "INSERT INTO users (username, full_name, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, full_name.strip(), hash_password(password), role),
            )
        except sqlite3.IntegrityError:
            return False, "That username is already taken."
    return True, f"Account created. Your role is: {role}."


def login(username, password, db_path=None):
    """Return the user as a dictionary if the login is correct, otherwise None."""
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    if row is not None and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def list_users(db_path=None):
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, username, full_name, role, created_at FROM users ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def _count_admins(conn):
    return conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]


def change_role(user_id, new_role, acting_user_id, db_path=None):
    """Promote or demote a user. Returns (ok, message)."""
    if new_role not in ("admin", "staff"):
        return False, "Role must be admin or staff."
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return False, "No user with that ID."
        if row["role"] == new_role:
            return False, f"That user is already {new_role}."
        if row["role"] == "admin" and _count_admins(conn) <= 1:
            return False, "You cannot demote the last remaining admin."
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    return True, f"User {user_id} is now {new_role}."


def delete_user(user_id, acting_user_id, db_path=None):
    """Delete a user account. Returns (ok, message)."""
    if user_id == acting_user_id:
        return False, "You cannot delete your own account while logged in."
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return False, "No user with that ID."
        if row["role"] == "admin" and _count_admins(conn) <= 1:
            return False, "You cannot delete the last remaining admin."
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return True, f"User {user_id} deleted."


def change_password(user_id, old_password, new_password, db_path=None):
    """Let a user change their own password. Returns (ok, message)."""
    ok, message = check_password_strength(new_password)
    if not ok:
        return False, message
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None or not verify_password(old_password, row["password_hash"]):
            return False, "Current password is incorrect."
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id)
        )
    return True, "Password changed."
