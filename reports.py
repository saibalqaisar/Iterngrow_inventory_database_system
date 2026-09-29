"""reports.py - summary reports built with SQL, plus CSV export."""

import csv
import os
from datetime import datetime

from database import get_connection, BASE_DIR

REPORTS_DIR = os.path.join(BASE_DIR, "reports")


def inventory_summary(low_stock_limit=10, db_path=None):
    """Overall numbers for the whole inventory."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS products, "
            "       COALESCE(SUM(quantity), 0) AS units, "
            "       COALESCE(SUM(quantity * price), 0) AS stock_value, "
            "       COALESCE(SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END), 0) AS out_of_stock, "
            "       COALESCE(SUM(CASE WHEN quantity > 0 AND quantity <= ? THEN 1 ELSE 0 END), 0) AS low_stock "
            "FROM products",
            (low_stock_limit,),
        ).fetchone()
    return dict(row)


def category_summary(db_path=None):
    """One line per category: how many products, units and total value."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) AS products, SUM(quantity) AS units, "
            "       SUM(quantity * price) AS stock_value "
            "FROM products GROUP BY category ORDER BY stock_value DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def low_stock_items(limit=10, db_path=None):
    """Products that are running out (quantity at or below the limit)."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE quantity <= ? ORDER BY quantity ASC, name", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def export_report_csv(low_stock_limit=10, db_path=None, reports_dir=None):
    """Write the full inventory to a CSV file and return its path."""
    folder = reports_dir or REPORTS_DIR
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, f"inventory_report_{stamp}.csv")

    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, category, quantity, price, quantity * price AS stock_value, "
            "       CASE WHEN quantity = 0 THEN 'Out of stock' "
            "            WHEN quantity <= ? THEN 'Low stock' ELSE 'OK' END AS status "
            "FROM products ORDER BY category, name",
            (low_stock_limit,),
        ).fetchall()

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Name", "Category", "Quantity", "Price", "Stock Value", "Status"])
        for r in rows:
            writer.writerow([r["id"], r["name"], r["category"], r["quantity"],
                             f"{r['price']:.2f}", f"{r['stock_value']:.2f}", r["status"]])
    return path
