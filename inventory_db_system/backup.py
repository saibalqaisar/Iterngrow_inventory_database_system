"""backup.py - database backup and restore.

Uses SQLite's own backup feature, which gives a consistent copy of the
database even if it is being used. Backups go into backups/ with a
timestamp in the name.
"""

import os
import sqlite3
from datetime import datetime

from database import BASE_DIR, DB_PATH

BACKUP_DIR = os.path.join(BASE_DIR, "backups")


def create_backup(db_path=None, backup_dir=None, prefix="inventory"):
    """Copy the database into backups/. Returns the backup file path."""
    source_path = db_path or DB_PATH
    folder = backup_dir or BACKUP_DIR
    if not os.path.exists(source_path):
        raise FileNotFoundError("There is no database to back up yet.")
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    target_path = os.path.join(folder, f"{prefix}_{stamp}.db")

    source = sqlite3.connect(source_path)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return target_path


def list_backups(backup_dir=None):
    """Backup file names, newest first."""
    folder = backup_dir or BACKUP_DIR
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(".db")]
    return sorted(files, reverse=True)


def restore_backup(filename, db_path=None, backup_dir=None):
    """Replace the current database with a chosen backup.

    Safety steps: the name must be one of our backup files (no folder tricks),
    the backup must pass SQLite's integrity check, and the current database
    is backed up first so nothing is lost. Returns (ok, message).
    """
    target_path = db_path or DB_PATH
    folder = backup_dir or BACKUP_DIR
    if filename not in list_backups(folder):
        return False, "That backup file does not exist."
    backup_path = os.path.join(folder, filename)

    check = sqlite3.connect(backup_path)
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.DatabaseError:
        result = "not a database"
    finally:
        check.close()
    if result != "ok":
        return False, "That backup file is damaged and cannot be restored."

    if os.path.exists(target_path):
        create_backup(target_path, folder, prefix="before_restore")

    source = sqlite3.connect(backup_path)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return True, "Database restored. Your previous data was saved as a 'before_restore' backup."
