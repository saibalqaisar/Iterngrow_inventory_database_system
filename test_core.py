"""Automated tests. Run with: python -m unittest discover tests
Every test uses its own temporary database, so your real data is never touched."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backup
import products
import reports
import users
from database import init_db, get_connection
from permissions import can
from security import hash_password, verify_password, check_password_strength


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")
        self.backups = os.path.join(self.tmp.name, "backups")
        init_db(self.db)

    def tearDown(self):
        self.tmp.cleanup()


class TestSecurity(unittest.TestCase):
    def test_hash_is_not_the_password_and_verifies(self):
        stored = hash_password("Secret123")
        self.assertNotIn("Secret123", stored)
        self.assertTrue(verify_password("Secret123", stored))
        self.assertFalse(verify_password("Wrong123", stored))

    def test_same_password_gives_different_hashes(self):
        self.assertNotEqual(hash_password("Secret123"), hash_password("Secret123"))

    def test_password_rules(self):
        self.assertFalse(check_password_strength("short1")[0])
        self.assertFalse(check_password_strength("onlyletters")[0])
        self.assertFalse(check_password_strength("12345678")[0])
        self.assertTrue(check_password_strength("Longenough1")[0])


class TestUsers(BaseTest):
    def test_first_user_is_admin_then_staff(self):
        users.register_user("first_user", "First User", "Password1", self.db)
        users.register_user("second_user", "Second User", "Password2", self.db)
        roles = {u["username"]: u["role"] for u in users.list_users(self.db)}
        self.assertEqual(roles["first_user"], "admin")
        self.assertEqual(roles["second_user"], "staff")

    def test_password_is_stored_hashed(self):
        users.register_user("hash_check", "Hash Check", "Password1", self.db)
        with get_connection(self.db) as conn:
            stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
        self.assertNotEqual(stored, "Password1")
        self.assertTrue(stored.startswith("pbkdf2_sha256$"))

    def test_duplicate_username_rejected_case_insensitive(self):
        users.register_user("dupe_user", "A", "Password1", self.db)
        ok, _ = users.register_user("DUPE_USER", "B", "Password1", self.db)
        self.assertFalse(ok)

    def test_login(self):
        users.register_user("login_user", "Login User", "Password1", self.db)
        self.assertIsNotNone(users.login("login_user", "Password1", self.db))
        self.assertIsNone(users.login("login_user", "Nope1234", self.db))
        self.assertIsNone(users.login("nobody", "Password1", self.db))

    def test_sql_injection_attempt_fails(self):
        users.register_user("real_user", "Real User", "Password1", self.db)
        self.assertIsNone(users.login("' OR '1'='1", "' OR '1'='1", self.db))

    def test_cannot_remove_last_admin(self):
        users.register_user("only_admin", "Only Admin", "Password1", self.db)
        admin_id = users.list_users(self.db)[0]["id"]
        self.assertFalse(users.change_role(admin_id, "staff", admin_id, self.db)[0])
        self.assertFalse(users.delete_user(admin_id, 999, self.db)[0])

    def test_cannot_delete_yourself(self):
        users.register_user("admin_one", "Admin One", "Password1", self.db)
        users.register_user("staff_one", "Staff One", "Password1", self.db)
        admin_id = users.list_users(self.db)[0]["id"]
        self.assertFalse(users.delete_user(admin_id, admin_id, self.db)[0])

    def test_change_password(self):
        users.register_user("pw_user", "Pw User", "Password1", self.db)
        uid = users.list_users(self.db)[0]["id"]
        self.assertFalse(users.change_password(uid, "WrongOld1", "Newpass99", self.db)[0])
        self.assertTrue(users.change_password(uid, "Password1", "Newpass99", self.db)[0])
        self.assertIsNotNone(users.login("pw_user", "Newpass99", self.db))


class TestPermissions(unittest.TestCase):
    def test_roles(self):
        admin = {"role": "admin"}
        staff = {"role": "staff"}
        self.assertTrue(can(admin, "delete_product"))
        self.assertFalse(can(staff, "delete_product"))
        self.assertFalse(can(staff, "backup_database"))
        self.assertTrue(can(staff, "add_product"))
        self.assertFalse(can(None, "add_product"))


class TestProducts(BaseTest):
    def setUp(self):
        super().setUp()
        products.add_product("Alpha Item", "Group A", 5, 10.0, None, self.db)
        products.add_product("Beta Item", "Group A", 50, 2.5, None, self.db)
        products.add_product("Gamma Item", "Group B", 0, 100.0, None, self.db)

    def test_add_and_duplicate(self):
        ok, _ = products.add_product("alpha item", "Group A", 1, 1.0, None, self.db)
        self.assertFalse(ok)
        self.assertEqual(len(products.list_products(db_path=self.db)), 3)

    def test_update_and_delete(self):
        pid = products.list_products(db_path=self.db)[0]["id"]
        self.assertTrue(products.update_product(pid, db_path=self.db, quantity=77)[0])
        self.assertEqual(products.get_product(pid, self.db)["quantity"], 77)
        self.assertTrue(products.delete_product(pid, self.db)[0])
        self.assertIsNone(products.get_product(pid, self.db))
        self.assertFalse(products.delete_product(pid, self.db)[0])

    def test_negative_quantity_blocked_by_database(self):
        pid = products.list_products(db_path=self.db)[0]["id"]
        ok, message = products.update_product(pid, db_path=self.db, quantity=-5)
        self.assertFalse(ok)
        self.assertIn("negative", message)
        ok, message = products.add_product("Bad Item", "Group A", -1, 5.0, None, self.db)
        self.assertFalse(ok)
        self.assertIn("negative", message)

    def test_duplicate_name_message_on_update(self):
        first, second = products.list_products(db_path=self.db)[:2]
        ok, message = products.update_product(second["id"], db_path=self.db, name=first["name"])
        self.assertFalse(ok)
        self.assertIn("name", message)

    def test_search(self):
        self.assertEqual(len(products.search_products("beta", self.db)), 1)
        self.assertEqual(len(products.search_products("group a", self.db)), 2)
        self.assertEqual(len(products.search_products("zzz", self.db)), 0)

    def test_filters(self):
        self.assertEqual(len(products.filter_products(category="Group A", db_path=self.db)), 2)
        self.assertEqual(len(products.filter_products(min_price=50, db_path=self.db)), 1)
        self.assertEqual(len(products.filter_products(max_quantity=5, db_path=self.db)), 2)
        both = products.filter_products(category="Group A", max_quantity=5, db_path=self.db)
        self.assertEqual([p["name"] for p in both], ["Alpha Item"])

    def test_sorting(self):
        names = [p["name"] for p in products.list_products("price", True, self.db)]
        self.assertEqual(names[0], "Gamma Item")

    def test_reports(self):
        summary = reports.inventory_summary(10, self.db)
        self.assertEqual(summary["products"], 3)
        self.assertEqual(summary["units"], 55)
        self.assertEqual(summary["stock_value"], 5 * 10.0 + 50 * 2.5)
        self.assertEqual(summary["out_of_stock"], 1)
        self.assertEqual(summary["low_stock"], 1)
        self.assertEqual(len(reports.category_summary(self.db)), 2)
        path = reports.export_report_csv(10, self.db, os.path.join(self.tmp.name, "rep"))
        self.assertTrue(os.path.exists(path))


class TestBackup(BaseTest):
    def test_backup_and_restore(self):
        products.add_product("Keep Me", "Group A", 1, 1.0, None, self.db)
        path = backup.create_backup(self.db, self.backups)
        self.assertTrue(os.path.exists(path))
        products.delete_product(products.list_products(db_path=self.db)[0]["id"], self.db)
        self.assertEqual(len(products.list_products(db_path=self.db)), 0)
        name = backup.list_backups(self.backups)[0]
        ok, _ = backup.restore_backup(name, self.db, self.backups)
        self.assertTrue(ok)
        self.assertEqual(len(products.list_products(db_path=self.db)), 1)

    def test_restore_rejects_unknown_file(self):
        ok, _ = backup.restore_backup("../../evil.db", self.db, self.backups)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
