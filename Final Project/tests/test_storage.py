"""Regression checks for damaged saved data, using the normal console entry point."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from grocery_system.storage import load_inventory, save_inventory
from grocery_system.inventory import Inventory


def starter_inventory():
    inventory = Inventory()
    inventory.add_product("1", "Rice", 1500)
    inventory.receive_batch("1", 20)
    return inventory


MAIN = Path(__file__).resolve().parents[1] / "main.py"


class StorageValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "inventory.json"
        save_inventory(self.path, starter_inventory())
        self.valid = json.loads(self.path.read_text())

    def reject(self, data):
        original = json.dumps(data)
        self.path.write_text(original)
        result = subprocess.run(
            [sys.executable, str(MAIN), "--data", str(self.path)], input="0\n",
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("inventory file contains invalid data", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.path.read_text(), original)

    def test_invalid_prices_and_quantities(self):
        for field, values, collection in [
            ("price_sen", [-100, 0, True, "750", 9999901], "products"),
            ("quantity", [-1, True, "two", 1.5], "batches"),
            ("batch_id", [0, -1, True], "batches"),
        ]:
            for value in values:
                with self.subTest(field=field, value=value):
                    data = deepcopy(self.valid)
                    data[collection][0][field] = value
                    self.reject(data)

    def test_invalid_identity_and_structure(self):
        cases = []
        for collection in ("products", "batches"):
            data = deepcopy(self.valid)
            data[collection].append(deepcopy(data[collection][0]))
            cases.append(data)
        data = deepcopy(self.valid)
        data["batches"][0]["product_code"] = "missing"
        cases.append(data)
        data = deepcopy(self.valid)
        data["products"][0]["name"] = ""
        cases.append(data)
        data = deepcopy(self.valid)
        data["batches"][0]["expiry"] = "2026-02-30"
        cases.append(data)
        cases.extend([None, [], {"products": {}}])
        for index, data in enumerate(cases):
            with self.subTest(case=index):
                self.reject(data)

    def test_invalid_discard_references_and_values(self):
        entry = {
            "product_code": "1", "batch_id": 1, "recorded_on": "2026-11-14",
            "reason": "Damaged", "quantity": 1, "unit_price_sen": 1500,
        }
        for field, value in [
            ("product_code", "2"), ("batch_id", 99), ("quantity", 0),
            ("unit_price_sen", -1), ("reason", "Unknown"),
            ("recorded_on", "2026-02-30"), ("reason", "Expired"),
        ]:
            with self.subTest(field=field):
                data = deepcopy(self.valid)
                changed = dict(entry)
                changed[field] = value
                data["waste_entries"].append(changed)
                self.reject(data)

    def test_valid_undated_stock_and_discard_history_round_trip(self):
        inventory = starter_inventory()
        inventory.record_waste(1, 2, "Damaged", date.today())
        save_inventory(self.path, inventory)
        restored = load_inventory(self.path)
        self.assertEqual(restored, inventory)


if __name__ == "__main__":
    unittest.main()
