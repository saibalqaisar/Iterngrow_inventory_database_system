"""permissions.py - role-based access control (RBAC).

One place decides who may do what. The menu asks can(user, action)
before showing or running anything, so adding a new rule means
changing just this file.
"""

ADMIN = "admin"
STAFF = "staff"

PERMISSIONS = {
    "add_product":      {ADMIN, STAFF},
    "view_products":    {ADMIN, STAFF},
    "search_products":  {ADMIN, STAFF},
    "filter_products":  {ADMIN, STAFF},
    "update_product":   {ADMIN, STAFF},
    "delete_product":   {ADMIN},
    "view_reports":     {ADMIN, STAFF},
    "change_password":  {ADMIN, STAFF},
    "manage_users":     {ADMIN},
    "backup_database":  {ADMIN},
    "restore_database": {ADMIN},
}


def can(user, action):
    """True if this logged-in user's role is allowed to perform the action."""
    if user is None:
        return False
    return user["role"] in PERMISSIONS.get(action, set())
