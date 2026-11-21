"""Run a staff shift against temporary seeded stock and reopen it the next session."""
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from grocery_system.storage import load_inventory, save_inventory
from grocery_system.validation import format_display_date
from main import demo_inventory


class DemoShiftTests(unittest.TestCase):
    def test_alerts_across_calendar_boundaries(self):
        for today in (date(2024, 2, 29), date(2026, 1, 1)):
            with self.subTest(today=today):
                stock = demo_inventory(today)
                self.assertEqual(len(stock.products), 12)
                self.assertEqual(len(stock.batches), 14)
                alerts = stock.expiry_alerts(today)
                self.assertEqual([(b.expiry - today).days for b in alerts], [-2, 0, 1, 2, 3])
                self.assertEqual(stock.available_quantity("SP", today, True), 0)
                self.assertEqual(stock.available_quantity("6", today, True), 16)

    def test_shift_and_restart(self):
        today = date.today()
        expiry = format_display_date(today + timedelta(days=10))
        with TemporaryDirectory() as folder:
            path = Path(folder) / "example.json"
            save_inventory(path, demo_inventory(today))
            command = [sys.executable, str(Path(__file__).resolve().parents[1] / "main.py"), "--data", str(path)]
            steps = [
                "8", "3", "2", "999",           # Reject an oversized cart request.
                "3", "2", "7", "5", "maybe", "NO", "5", " Yes ",  # A single sale uses both milk batches.
                "12", "3", "1", "Pantry", "y",  # Reject donation from the expired batch.
                "12", "2", "2", "Pantry", "ye", "yes",
                "9", "3", "1", "1", "", "Y",
                "7", "6", expiry, "6",
                "11", "13", "3", expiry,       # Verify just three of eight undated bags.
                "13", "0",
            ]
            first = subprocess.run(command, input="\n".join(steps) + "\n", text=True,
                                   capture_output=True, check=True, timeout=10)
            for message in ("exceeds the available stock", "Purchase cancelled", "Batch #1: 5",
                            "Batch #2: 2", "Choose a batch with a verified expiry"):
                self.assertIn(message, first.stdout)
            restart = subprocess.run(command, input="13\n0\n", text=True, capture_output=True,
                                     check=True, timeout=10)
            for total in ("Remaining stock: 152 units", "Sold: 50 units (retail value RM 313.30)",
                          "Donated: 9 units (retail value RM 41.40)",
                          "Discarded: 6 units (retail value RM 19.80)"):
                self.assertIn(total, restart.stdout)
            stock = load_inventory(path)
            self.assertEqual(stock.batches[13].quantity, 5)
            self.assertEqual(stock.available_quantity("SP", today, True), 3)
