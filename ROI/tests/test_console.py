"""Run the grocery menu from a temporary working directory for each test."""

import json
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


MAIN = Path(__file__).resolve().parents[1] / "main.py"


class GroceryConsoleTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.inventory_file = self.folder / "inventory.json"
        self.today = date.today()

    def run_console(self, *entries, mode=None, expected_status=0):
        command = [sys.executable, str(MAIN)]
        if mode:
            command.append(mode)
        result = subprocess.run(
            command,
            cwd=self.folder,
            input="\n".join(str(entry) for entry in entries) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, expected_status, result.stdout + result.stderr)
        if expected_status == 0:
            self.assertEqual(result.stderr, "")
        return result.stdout + result.stderr

    def read_inventory(self):
        return json.loads(self.inventory_file.read_text(encoding="utf-8"))

    def milk_rows(self, output):
        return [
            line for line in output.splitlines()
            if line.split()[:3] == ["2", "Milk", "7.50"]
        ]

    def test_assignment_checkout_cancel_confirm_and_restart(self):
        output = self.run_console(
            1, 3, 2, 2, 4, 5, "n", 1, 5, "y", 4, 1, 0,
        )
        for name in ("Rice", "Milk", "Bread", "Eggs", "Cooking Oil"):
            self.assertIn(name, output)
        self.assertEqual(output.count("Total: RM 15.00"), 3)
        self.assertIn("Purchase cancelled", output)
        self.assertEqual(output.count("Purchase saved. Stock updated."), 1)
        self.assertIn("Your cart is empty.", output)
        self.assertEqual([row.split()[-1] for row in self.milk_rows(output)], ["15", "15", "15", "13"])
        self.assertEqual(self.milk_rows(self.run_console(1, 0))[0].split()[-1], "13")

    def test_assignment_rejects_invalid_entries_and_saves_new_product(self):
        output = self.run_console(
            "x", 3, "bad", 3, 2, "two", 3, 2, 0, 3, 2, 2, 3, 2, 14, 6, 4,
            2, 2, 2, "A01", "Apples", "NaN", 2, "A01", "Apples", "2.351",
            2, "A01", "Apples", "2.35", -1, 2, "A01", "Apples", "2.35", 6, 0,
        )
        for message in (
            "Choose one of the listed options.", "Invalid product ID.", "valid whole number.",
            "whole number of at least 1", "cart quantity exceeds", "Cart cleared.",
            "Your cart is empty.", "product ID already exists", "Price must be between",
            "at most two decimal places", "whole number of at least 0", "Product registered.",
        ):
            self.assertIn(message, output)
        output = self.run_console(1, 3, "a01", 3, 4, 0)
        self.assertIn("Apples", output)
        self.assertIn("Total: RM 7.05", output)

    def test_final_project_can_split_stock_saved_in_assignment_2(self):
        self.run_console(3, 2, 2, 5, "y", 0)
        before_dates = self.run_console(1, 3, 2, 1, 0, mode="--final-project")
        self.assertIn("Verify expiry before sale", before_dates)
        self.assertIn("cart quantity exceeds", before_dates)
        first_date = self.today + timedelta(days=2)
        second_date = self.today + timedelta(days=7)
        output = self.run_console(
            11, 2, 14, first_date,
            11, 2, 5, first_date,
            11, 2, 8, second_date,
            8, 3, 2, 6, 5, "y", 1, 0, mode="--final-project",
        )
        self.assertIn("within the batch stock.", output)
        self.assertIn("Due in 2 day(s)", output)
        self.assertIn("Due in 7 day(s)", output)
        self.assertIn("Total: RM 45.00", output)
        self.assertIn("Batch #6: 5 unit(s) sold\nBatch #2: 1 unit(s) sold", output)
        milk_batches = [batch for batch in self.read_inventory()["batches"] if batch["product_code"] == "2"]
        self.assertEqual(sum(batch["quantity"] for batch in milk_batches), 7)
        self.assertIn("Run with --final-project.", self.run_console(0, expected_status=1))

    def test_demo_alerts_checkout_discard_and_reset(self):
        output = self.run_console(
            8, 3, 6, 1, 3, 2, 6, 5, "y", 9, 3, 5, 1,
            9, 3, 4, 1, 10, 1, 8, 0, mode="--demo",
        )
        for message in (
            "Due in 2 day(s)", "Expired", "cart quantity exceeds", "Total: RM 45.00",
            "Batch #1: 5 unit(s) sold\nBatch #2: 1 unit(s) sold", "within the batch stock.",
            "Total discarded units: 4", "Estimated retail value: RM 10.00",
            "No stocked batches are expired or due within 7 days.",
        ):
            self.assertIn(message, output)
        self.assertEqual(self.milk_rows(output)[-1].split()[-1], "14")
        self.assertFalse(self.inventory_file.exists())
        fresh_demo = self.run_console(10, 0, mode="--demo")
        self.assertIn("No food waste has been recorded.", fresh_demo)

    def test_dates_revalidation_and_persistence_in_final_project(self):
        yesterday = self.today - timedelta(days=1)
        day_seven = self.today + timedelta(days=7)
        day_eight = self.today + timedelta(days=8)
        output = self.run_console(
            2, "Y01", "Yogurt", "2.50", 7, "Y01", "2026-02-30",
            7, "Y01", yesterday, 4, 9, 1, 4, 1,
            7, "Y01", self.today, 1, 7, "Y01", day_seven, 1, 7, "Y01", day_eight, 1,
            8, 3, "Y01", 3, 9, 2, 1, 1, 9, 2, 1, 2, 5, "y", 0,
            mode="--final-project",
        )
        for message in (
            "Enter a valid date in YYYY-MM-DD format.", "Expires today", "Due in 7 day(s)",
            "Expired discards require a verified date before today.", "Insufficient sellable stock",
        ):
            self.assertIn(message, output)
        self.assertNotIn(str(day_eight), output)
        self.assertNotIn("Purchase saved.", output)
        data = self.read_inventory()
        self.assertEqual([batch["quantity"] for batch in data["batches"]], [0, 0, 1, 1])
        output = self.run_console(1, 10, 0, mode="--final-project")
        self.assertIn("Total discarded units: 5", output)
        self.assertIn("Estimated retail value: RM 12.50", output)
        self.assertIn("Damaged", output)
        self.assertIn("Expired", output)

    def test_invalid_json_is_preserved(self):
        self.inventory_file.write_text("{bad json", encoding="utf-8")
        output = self.run_console(0, expected_status=1)
        self.assertIn("Unable to continue with the inventory file", output)
        self.assertEqual(self.inventory_file.read_text(encoding="utf-8"), "{bad json")


if __name__ == "__main__":
    unittest.main()
