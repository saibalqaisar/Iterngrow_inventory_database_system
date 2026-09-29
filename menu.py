"""menu.py - the menu driven interface for the Inventory Database System.

This file only talks to the user (print / input). All real work is
done by users.py, products.py, reports.py and backup.py, and permissions.py
decides which menu options each role can see.
"""

import validators as check
import users
import products
import reports
import backup
from database import init_db
from permissions import can

MAX_LOGIN_ATTEMPTS = 3


# ---------- display helpers ----------
def print_products(items):
    if not items:
        print("\n  No products found.")
        return
    print(f"\n  {'ID':<5}{'Name':<24}{'Category':<16}{'Qty':<7}{'Price':<11}{'Value'}")
    print("  " + "-" * 72)
    for p in items:
        value = p["quantity"] * p["price"]
        print(f"  {p['id']:<5}{p['name'][:22]:<24}{p['category'][:14]:<16}"
              f"{p['quantity']:<7}{p['price']:<11,.2f}{value:,.2f}")
    print(f"\n  {len(items)} product(s) shown.")


def print_users(items):
    print(f"\n  {'ID':<5}{'Username':<22}{'Full name':<26}{'Role':<8}{'Created'}")
    print("  " + "-" * 76)
    for u in items:
        print(f"  {u['id']:<5}{u['username']:<22}{u['full_name'][:24]:<26}"
              f"{u['role']:<8}{u['created_at']}")


def choose_sort():
    print("  Sort by: 1) Name  2) Category  3) Quantity  4) Price")
    choice = check.get_int("  Choice: ", 1, 4)
    sort_by = {1: "name", 2: "category", 3: "quantity", 4: "price"}[choice]
    descending = check.get_yes_no("  Highest first? (y/n): ")
    return sort_by, descending


# ---------- authentication screens ----------
def register_screen():
    print("\n--- Register New Account ---")
    if users.count_users() == 0:
        print("  No accounts exist yet. The first account becomes the administrator.")
    full_name = check.get_name("  Full name: ")
    username = check.get_text("  Username (3-20 letters/numbers/_): ")
    print("  Password: at least 8 characters with a letter and a number.")
    print("  (Typing is hidden - that is normal.)")
    password = check.get_password("  Password: ")
    confirm = check.get_password("  Confirm password: ")
    if password != confirm:
        print("  Error: passwords do not match.")
        return
    ok, message = users.register_user(username, full_name, password)
    print(f"  {message}")


def login_screen():
    print("\n--- Login ---")
    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        username = check.get_text("  Username: ")
        password = check.get_password("  Password: ")
        user = users.login(username, password)
        if user:
            print(f"\n  Welcome, {user['full_name']}! (role: {user['role']})")
            return user
        left = MAX_LOGIN_ATTEMPTS - attempt
        if left:
            print(f"  Wrong username or password. {left} attempt(s) left.")
    print("  Too many failed attempts. Returning to the main screen.")
    return None


# ---------- product features ----------
def add_product_screen(user):
    print("\n--- Add Product ---")
    name = check.get_text("  Product name: ")
    existing = products.list_categories()
    if existing:
        print("  Existing categories: " + ", ".join(existing))
    category = check.get_text("  Category: ").title()
    quantity = check.get_int("  Quantity in stock (0-1000000): ", 0, 1_000_000)
    price = check.get_float("  Price per unit (0-10000000): ", 0, 10_000_000)
    ok, message = products.add_product(name, category, quantity, price, user["id"])
    print(f"  {message}")


def view_products_screen(user):
    print("\n--- All Products ---")
    sort_by, descending = choose_sort()
    print_products(products.list_products(sort_by, descending))


def search_screen(user):
    print("\n--- Search Products ---")
    term = check.get_text("  Search by name or category: ")
    print_products(products.search_products(term))


def filter_screen(user):
    print("\n--- Filter Products (press Enter to skip any filter) ---")
    categories = products.list_categories()
    if not categories:
        print("  There are no products yet.")
        return
    print("  Categories: " + ", ".join(categories))
    category = input("  Category (exact name): ").strip() or None
    min_price = check.get_optional_float("  Minimum price: ", 0, 10_000_000)
    max_price = check.get_optional_float("  Maximum price: ", 0, 10_000_000)
    max_quantity = check.get_optional_int("  Quantity at most: ", 0, 1_000_000)
    sort_by, descending = choose_sort()
    print_products(products.filter_products(category, min_price, max_price,
                                            max_quantity, sort_by, descending))


def update_product_screen(user):
    print("\n--- Update Product ---")
    product_id = check.get_int("  Product ID to update: ", 1, 10**9)
    product = products.get_product(product_id)
    if product is None:
        print("  No product with that ID.")
        return
    print_products([product])
    print("  Press Enter to keep the current value.")
    name = input(f"  New name [{product['name']}]: ").strip() or None
    category = input(f"  New category [{product['category']}]: ").strip().title() or None
    quantity = check.get_optional_int(f"  New quantity [{product['quantity']}]: ", 0, 1_000_000)
    price = check.get_optional_float(f"  New price [{product['price']:.2f}]: ", 0, 10_000_000)
    ok, message = products.update_product(product_id, name=name, category=category,
                                          quantity=quantity, price=price)
    print(f"  {message}")


def delete_product_screen(user):
    print("\n--- Delete Product ---")
    product_id = check.get_int("  Product ID to delete: ", 1, 10**9)
    product = products.get_product(product_id)
    if product is None:
        print("  No product with that ID.")
        return
    print_products([product])
    if check.get_yes_no("  Delete this product permanently? (y/n): "):
        ok, message = products.delete_product(product_id)
        print(f"  {message}")
    else:
        print("  Delete cancelled.")


# ---------- reports ----------
def reports_screen(user):
    print("\n--- Reports ---")
    limit = check.get_optional_int("  Low stock limit (press Enter for 10): ", 0, 1_000_000)
    limit = 10 if limit is None else limit

    s = reports.inventory_summary(limit)
    print("\n  INVENTORY SUMMARY")
    low_label = f"Low stock (<= {limit})"
    print(f"    {'Products':<22}: {s['products']}")
    print(f"    {'Total units':<22}: {s['units']}")
    print(f"    {'Total stock value':<22}: {s['stock_value']:,.2f}")
    print(f"    {'Out of stock':<22}: {s['out_of_stock']}")
    print(f"    {low_label:<22}: {s['low_stock']}")

    categories = reports.category_summary()
    if categories:
        print("\n  BY CATEGORY")
        print(f"    {'Category':<18}{'Products':<10}{'Units':<8}{'Value'}")
        for c in categories:
            print(f"    {c['category'][:16]:<18}{c['products']:<10}{c['units']:<8}{c['stock_value']:,.2f}")

    low = reports.low_stock_items(limit)
    if low:
        print(f"\n  LOW STOCK ITEMS (quantity <= {limit})")
        print_products(low)

    if s["products"] and check.get_yes_no("\n  Export full report to a CSV file? (y/n): "):
        path = reports.export_report_csv(limit)
        print(f"  Report saved to: {path}")


# ---------- account features ----------
def change_password_screen(user):
    print("\n--- Change My Password ---")
    old = check.get_password("  Current password: ")
    new = check.get_password("  New password: ")
    confirm = check.get_password("  Confirm new password: ")
    if new != confirm:
        print("  Error: new passwords do not match.")
        return
    ok, message = users.change_password(user["id"], old, new)
    print(f"  {message}")


def manage_users_screen(user):
    while True:
        print("\n--- Manage Users ---")
        print_users(users.list_users())
        print("\n  1. Change a user's role")
        print("  2. Delete a user")
        print("  3. Back")
        choice = check.get_int("  Choice: ", 1, 3)
        if choice == 3:
            return
        target_id = check.get_int("  User ID: ", 1, 10**9)
        if choice == 1:
            role = "admin" if check.get_yes_no("  Make this user an admin? (y = admin, n = staff): ") else "staff"
            ok, message = users.change_role(target_id, role, user["id"])
        else:
            if not check.get_yes_no("  Delete this user permanently? (y/n): "):
                print("  Cancelled.")
                continue
            ok, message = users.delete_user(target_id, user["id"])
        print(f"  {message}")


# ---------- backup ----------
def backup_screen(user):
    print("\n--- Database Backup ---")
    try:
        path = backup.create_backup()
        print(f"  Backup saved: {path}")
    except FileNotFoundError as error:
        print(f"  {error}")


def restore_screen(user):
    print("\n--- Restore Database From Backup ---")
    files = backup.list_backups()
    if not files:
        print("  No backups found. Create one first.")
        return
    for number, name in enumerate(files, start=1):
        print(f"  {number}. {name}")
    choice = check.get_int("  Backup number to restore: ", 1, len(files))
    print("  WARNING: this replaces the current database with the backup.")
    print("  Your current data will be saved as a 'before_restore' backup first.")
    if not check.get_yes_no("  Continue? (y/n): "):
        print("  Cancelled.")
        return
    ok, message = backup.restore_backup(files[choice - 1])
    print(f"  {message}")


# ---------- role-based menu ----------
# (label shown, permission needed, function to run)
MENU_ITEMS = [
    ("Add Product",             "add_product",      add_product_screen),
    ("View All Products",       "view_products",    view_products_screen),
    ("Search Products",         "search_products",  search_screen),
    ("Filter Products",         "filter_products",  filter_screen),
    ("Update Product",          "update_product",   update_product_screen),
    ("Delete Product",          "delete_product",   delete_product_screen),
    ("Reports",                 "view_reports",     reports_screen),
    ("Change My Password",      "change_password",  change_password_screen),
    ("Manage Users",            "manage_users",     manage_users_screen),
    ("Backup Database",         "backup_database",  backup_screen),
    ("Restore Database",        "restore_database", restore_screen),
]


def main_menu(user):
    """Show only the options this user's role is allowed to use."""
    while True:
        allowed = [item for item in MENU_ITEMS if can(user, item[1])]
        print("\n" + "=" * 46)
        print(f"   INVENTORY SYSTEM  |  {user['username']} ({user['role']})")
        print("=" * 46)
        for number, (label, _, _) in enumerate(allowed, start=1):
            print(f"  {number:>2}. {label}")
        logout_number = len(allowed) + 1
        print(f"  {logout_number:>2}. Logout")
        print("-" * 46)
        choice = check.get_int(f"  Enter your choice (1-{logout_number}): ", 1, logout_number)
        if choice == logout_number:
            print("\n  Logged out.")
            return
        allowed[choice - 1][2](user)


def start_screen():
    """Login / Register / Exit. Returns when the user chooses Exit."""
    while True:
        print("\n" + "=" * 46)
        print("      INVENTORY DATABASE SYSTEM")
        print("=" * 46)
        print("  1. Login")
        print("  2. Register")
        print("  3. Exit")
        print("-" * 46)
        choice = check.get_int("  Enter your choice (1-3): ", 1, 3)
        if choice == 3:
            print("\n  Goodbye!")
            return
        if choice == 2:
            register_screen()
        else:
            user = login_screen()
            if user:
                main_menu(user)


def run():
    init_db()
    try:
        start_screen()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Program interrupted. Your data is saved. Goodbye!")
