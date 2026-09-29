# Inventory Database System

A menu-driven console application in Python with a real SQLite database.
Users register and log in, and manage a product inventory with full CRUD,
search, filters and reports. Built as **Task 3** of the InternGrow Python
Programming Track.

## Features
- **User registration and login**
- **CRUD** on products: create, read, update, delete
- **Search** by product name or category
- **Filters**: category, price range, low quantity, with sorting
- **Reports**: inventory summary, category breakdown, low-stock list, CSV export

## Upgrade Features
- **Password hashing**: PBKDF2-HMAC-SHA256 with a random salt per user (no plain-text passwords)
- **Role-based access**: `admin` and `staff` roles; the first registered account becomes the admin
- **Database backup**: timestamped backups, plus restore with a safety backup first

## Security Notes
- Every SQL query uses `?` placeholders, which prevents SQL injection
- Database constraints (`UNIQUE`, `CHECK`) block duplicate names and negative quantity/price
- The last admin cannot be deleted or demoted; users cannot delete their own account
- Login is limited to 3 attempts

## Roles
| Action | Admin | Staff |
|--------|:-----:|:-----:|
| Add / view / search / filter / update products | Yes | Yes |
| Reports and CSV export | Yes | Yes |
| Change own password | Yes | Yes |
| Delete products | Yes | No |
| Manage users | Yes | No |
| Backup / restore database | Yes | No |

## Project Structure
| File | Purpose |
|------|---------|
| `main.py` | Starts the program |
| `menu.py` | Menus and user interaction |
| `database.py` | SQLite connection and table creation |
| `security.py` | Password hashing and password rules |
| `permissions.py` | Role-based access rules |
| `users.py` | Registration, login, user management |
| `products.py` | CRUD, search and filters |
| `reports.py` | Summary reports and CSV export |
| `backup.py` | Database backup and restore |
| `validators.py` | Safe input functions |
| `tests/` | 22 automated unit tests |

## How to Run
```bash
python main.py
```
Requires Python 3.8+. No external libraries needed (SQLite is built into Python).

On the first run, choose **Register**. The first account you create becomes the administrator.

## Run Tests
```bash
python -m unittest discover tests
```

## Skills Used
SQL, SQLite, CRUD, database connectivity, password hashing, role-based access, exception handling, modular design.

## Screenshots
Add your screenshots in a `screenshots/` folder and link them here.
