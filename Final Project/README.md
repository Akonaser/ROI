# Smart Grocery · Final Project

A single-user macOS stock manager for grocery staff. Staff can check dated stock, sell from the earliest eligible batch, record food handed to a recipient, and review waste by reason. Donation records support the project's SDG 2 focus by tracking food actually distributed.

Use Python 3.10 or later. The desktop interface uses Tkinter with the macOS Aqua theme when available.

From this folder, run `python3 gui.py --demo` for the desktop demo or `python3 main.py --demo` for the console demo. Demo data resets on exit. To use your own stock, omit `--demo`. Both interfaces open the same local surplus.json file, one session at a time.

The demo opens with a week of simulated sales, pantry donations and waste records for 12 groceries. The expiry dates move with the day you launch it.

In the demo, sell three units of Milk, then open **Stock Batches**, select the two remaining units in batch 1 and choose **Donate**. Enter the recipient and confirm. Open **Report** to review stock, sales, donated units and their retail value.

Run the tests with `python3 -m unittest discover -s tests -v`.
