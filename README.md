# Inventory Database System

A menu-driven console application in Python with a real SQLite database.
Users register and log in, and manage a product inventory with full CRUD,
search, filters and reports. Built as **Task 3** of the InternGrow Python
Programming Track.

## Features
- User registration and login
- CRUD on products: create, read, update, delete
- Search by product name or category
- Filters: category, price range, low quantity, with sorting
- Reports: inventory summary, category breakdown, low-stock list, CSV export

## Upgrade Features
- Password hashing: PBKDF2-HMAC-SHA256 with a random salt per user
- Role-based access: admin and staff roles (the first account becomes admin)
- Database backup: timestamped backups, plus restore with a safety backup first

## Security Notes
- Every SQL query uses `?` placeholders, which prevents SQL injection
- Database constraints (`UNIQUE`, `CHECK`) block duplicate names and negative values
- The last admin cannot be deleted or demoted
- Login is limited to 3 attempts

## How to Run
```bash
python main.py
```
Requires Python 3.8+. No external libraries needed.

## Run Tests
```bash
python -m unittest discover tests
```

## Skills Used
SQL, SQLite, CRUD, database connectivity, password hashing, role-based access, exception handling, modular design.
