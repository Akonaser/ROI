import subprocess
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from gui import GroceryApp
from grocery import activity_report
from grocery_system.storage import inventory_session, load_inventory, save_inventory
from grocery_system.inventory import Inventory


class SurplusTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "stock.json"
        self.today = date.today()
        # A small, fixed fixture keeps transaction tests independent of the demo menu.
        inventory = Inventory()
        inventory.add_product("2", "Milk", 750)
        inventory.add_product("6", "Yogurt", 250)
        inventory.receive_batch("2", 5, self.today + timedelta(days=2))
        inventory.receive_batch("2", 15, self.today + timedelta(days=12))
        inventory.receive_batch("6", 4, self.today - timedelta(days=1))
        self.inventory = inventory

    def test_distribution_and_waste_survive_restart(self):
        stock = self.inventory
        self.assertEqual(stock.checkout({"2": 3}, self.today, True), [(1, 3)])
        stock.donate(1, 2, "Campus Pantry", self.today)
        stock.record_waste(2, 1, "Damaged", self.today)
        save_inventory(self.path, stock)
        report = activity_report(load_inventory(self.path))
        for expected in ("Remaining stock: 18", "Sold: 3 units (retail value RM 22.50)",
                         "Donated: 2 units (retail value RM 15.00)", "Discarded: 1", "Campus Pantry"):
            self.assertIn(expected, report)

    def test_invalid_donations_preserve_stock(self):
        stock = self.inventory
        undated = stock.receive_batch("2", 4)
        for batch, quantity, recipient in ((undated, 1, "Pantry"), (3, 1, "Pantry"),
                                           (1, 6, "Pantry"), (1, 0, "Pantry"), (1, 2, " ")):
            before = stock.batches[batch].quantity
            with self.assertRaises(ValueError):
                stock.donate(batch, quantity, recipient, self.today)
            self.assertEqual(stock.batches[batch].quantity, before)
            self.assertEqual(stock.distributions, [])

    def test_console_cancel_then_confirm(self):
        save_inventory(self.path, self.inventory)
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "main.py"),
                                 "--data", str(self.path)], text=True, capture_output=True, check=True,
                                input="12\n1\n2\nPantry\nn\n12\n1\n2\nPantry\ny\n13\n0\n", timeout=10)
        self.assertIn("Donation cancelled.", result.stdout)
        self.assertIn("Donated: 2 units", result.stdout)
        self.assertEqual(load_inventory(self.path).batches[1].quantity, 3)

    def test_single_editor(self):
        with inventory_session(self.path):
            with self.assertRaises(ValueError), inventory_session(self.path):
                pass
        with inventory_session(self.path):
            pass

    @patch("gui.messagebox.askyesno", return_value=True)
    def test_gui_checkout(self, confirm):
        app = GroceryApp.__new__(GroceryApp)
        app.inventory, app.data_path = self.inventory, self.path
        app.track_expiry, app.cart = True, {"2": 3}
        app.refresh, app.status, app.root = Mock(), Mock(), Mock()
        app.checkout()
        self.assertEqual(app.cart, {})
        self.assertEqual(load_inventory(self.path).batches[1].quantity, 2)
