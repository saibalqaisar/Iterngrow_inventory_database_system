"""products.py - CRUD (Create, Read, Update, Delete), Search and Filters
for the products table."""

import sqlite3

from database import get_connection

# Only these columns may be used for sorting. Column names cannot be sent as
# ? placeholders, so we check them against this fixed list instead.
SORT_COLUMNS = {
    "id": "id",
    "name": "name",
    "category": "category",
    "quantity": "quantity",
    "price": "price",
}


def _integrity_message(error, duplicate_message):
    """The database raises IntegrityError for two different problems.
    UNIQUE = the name is already used. CHECK = a negative quantity or price."""
    if "UNIQUE" in str(error).upper():
        return duplicate_message
    return "Quantity and price cannot be negative."


def _order_clause(sort_by, descending):
    column = SORT_COLUMNS.get(sort_by, "name")
    direction = "DESC" if descending else "ASC"
    return f"ORDER BY {column} {direction}, id ASC"


# ---------- CREATE ----------
def add_product(name, category, quantity, price, user_id, db_path=None):
    """Insert a new product. Returns (ok, message)."""
    with get_connection(db_path) as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO products (name, category, quantity, price, created_by) "
                "VALUES (?, ?, ?, ?, ?)",
                (name.strip(), category.strip(), quantity, price, user_id),
            )
        except sqlite3.IntegrityError as error:
            return False, _integrity_message(error, "A product with that name already exists.")
    return True, f"Product added with ID {cursor.lastrowid}."


# ---------- READ ----------
def get_product(product_id, db_path=None):
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    return dict(row) if row else None


def list_products(sort_by="name", descending=False, db_path=None):
    with get_connection(db_path) as conn:
        rows = conn.execute(f"SELECT * FROM products {_order_clause(sort_by, descending)}").fetchall()
    return [dict(r) for r in rows]


def list_categories(db_path=None):
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()
    return [r["category"] for r in rows]


# ---------- UPDATE ----------
def update_product(product_id, db_path=None, **fields):
    """Update only the fields given: name, category, quantity, price.
    Returns (ok, message)."""
    allowed = ("name", "category", "quantity", "price")
    changes = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not changes:
        return False, "Nothing to update."
    # The column names come from our fixed 'allowed' list, the values are placeholders.
    set_clause = ", ".join(f"{column} = ?" for column in changes)
    values = list(changes.values()) + [product_id]
    with get_connection(db_path) as conn:
        try:
            cursor = conn.execute(
                f"UPDATE products SET {set_clause}, updated_at = datetime('now', 'localtime') "
                "WHERE id = ?",
                values,
            )
        except sqlite3.IntegrityError as error:
            return False, _integrity_message(error, "Another product already uses that name.")
        if cursor.rowcount == 0:
            return False, "No product with that ID."
    return True, "Product updated."


# ---------- DELETE ----------
def delete_product(product_id, db_path=None):
    with get_connection(db_path) as conn:
        cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        if cursor.rowcount == 0:
            return False, "No product with that ID."
    return True, "Product deleted."


# ---------- SEARCH ----------
def search_products(term, db_path=None):
    """Find products whose name or category contains the text typed."""
    pattern = f"%{term.strip()}%"
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY name",
            (pattern, pattern),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- FILTERS ----------
def filter_products(category=None, min_price=None, max_price=None, max_quantity=None,
                    sort_by="name", descending=False, db_path=None):
    """Combine any filters you like. A filter left as None is simply ignored."""
    conditions = []
    values = []
    if category:
        conditions.append("category = ?")
        values.append(category)
    if min_price is not None:
        conditions.append("price >= ?")
        values.append(min_price)
    if max_price is not None:
        conditions.append("price <= ?")
        values.append(max_price)
    if max_quantity is not None:
        conditions.append("quantity <= ?")
        values.append(max_quantity)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM products {where} {_order_clause(sort_by, descending)}", values
        ).fetchall()
    return [dict(r) for r in rows]
