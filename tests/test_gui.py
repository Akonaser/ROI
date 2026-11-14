"""Verify desktop transactions with mocked dialogs and temporary inventory files."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from gui import GroceryApp
from main import starter_inventory
from grocery_system.storage import load_inventory


class DesktopTransactionTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.app = GroceryApp.__new__(GroceryApp)
        self.app.root = Mock()
        self.app.inventory = starter_inventory()
        self.app.data_path = Path(temporary.name) / "inventory.json"
        self.app.cart = {"2": 2}
        self.app.track_expiry = False
        self.app.status = Mock()
        self.app.refresh = Mock()

    @patch("gui.messagebox.askyesno", return_value=True)
    def test_checkout_saves_stock_and_clears_cart(self, confirmation):
        self.app.checkout()
        saved = load_inventory(self.app.data_path)
        self.assertEqual(saved.batches[2].quantity, 13)
        self.assertEqual(self.app.cart, {})

    @patch("gui.messagebox.askyesno", return_value=False)
    def test_cancel_preserves_cart_and_stock(self, confirmation):
        self.app.checkout()
        self.assertEqual(self.app.inventory.batches[2].quantity, 15)
        self.assertEqual(self.app.cart, {"2": 2})
        self.assertFalse(self.app.data_path.exists())

    @patch("gui.messagebox.showerror")
    @patch("gui.save_inventory", side_effect=OSError("Disk full"))
    @patch("gui.messagebox.askyesno", return_value=True)
    def test_failed_save_preserves_cart_and_stock(self, confirmation, save, error):
        self.app.checkout()
        self.assertEqual(self.app.inventory.batches[2].quantity, 15)
        self.assertEqual(self.app.cart, {"2": 2})
        error.assert_called_once()
        self.app.refresh.assert_not_called()

    def test_register_product_saves_exact_price(self):
        fields = {}
        for key, value in {"code": "A01", "name": "Apples", "price": "2.35", "stock": "6"}.items():
            fields[key] = Mock()
            fields[key].get.return_value = value
        dialog, error = Mock(), Mock()
        self.app.save_product(fields, dialog, error)
        error.set.assert_not_called()
        saved = load_inventory(self.app.data_path)
        self.assertEqual(saved.products["A01"].price_sen, 235)
        self.assertEqual(saved.batches[6].quantity, 6)
        dialog.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
