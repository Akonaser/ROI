# Smart Grocery & Food Waste Management System

A Python console application for the Fundamentals of Computational Thinking course. Assignment 2 covers the original team catalogue, cart, billing and saved stock. The course final project adds batch expiry and waste tracking under **SDG 2 (Zero Hunger)**. Both use the same catalogue, inventory and checkout code.

## Assignment 2

Run from the `ROI` subfolder with Python 3.10 or later (enter `cd ROI` from the repository root):

```text
python3 main.py
```

The first run includes rice, milk, bread, eggs and cooking oil. Choose **3**, enter product **2** and quantity **2**, then choose **5** and confirm with **y**. The bill is RM 15.00. Choose **1** to see milk stock change from 15 to 13.

## Existing expiry and waste prototype

```text
python3 main.py --final-project
```

Register products, receive dated batches, check expiry alerts, then sell or record discards. The project alerts on stock expiring in seven days or less and excludes expired batches from checkout. For this coursework model, a verified date of today is still eligible. Shop procedures also apply when assessing stock.

The default `inventory.json` is shared between both versions. To carry over earlier stock, use option **11** to enter verified expiry dates. You can split an undated batch by entering the quantity with one verified date at a time. The final-project checkout excludes undated units until you verify their dates. Use `--data FILE` in an existing directory to keep a separate inventory. Run one session per file.

### Try the demo

```text
python3 main.py --demo
```

1. Choose **8**. Five units of milk expire in two days and four units of yogurt are already expired.
2. Choose **3**, enter product **2** and quantity **6**, then choose **5** and confirm with **y**. The bill is RM 45.00. Checkout draws five units from batch 1 and one from batch 2.
3. Choose **9**, then enter batch **3**, quantity **4** and reason **1**. Choose **10** to see four units and RM 10.00 in estimated retail value.
4. Choose **0** to exit. Demo mode uses temporary sample data.

## Source files

- `main.py` starts the console and routes menu actions.
- `grocery.py` validates inputs, calculates bills and formats inventory, checkout and waste results.
- `grocery_system/inventory.py` defines products, batches, waste entries and shared stock rules.
- `grocery_system/storage.py` loads and saves a local JSON file.

Retail value uses the selling price at the time each discard was recorded. Reports summarize the items recorded by staff.

## Run local tests in VS Code on macOS

Open the repository root in VS Code for its tasks. For manual terminal commands, enter `cd ROI` first. Use **Terminal → Run Task** to select **Grocery: Run all tests**, **Grocery: Run Assignment 2**, or **Grocery: Run final-project demo**. The tasks run in VS Code's integrated terminal and use the installed `python3`.

The test task uses temporary inventory files. Run the same suite directly from the integrated terminal with:

```text
python3 -m unittest discover -s tests -v
```

## Desktop app on macOS

Run `python3 gui.py`, or choose **Terminal → Run Task → Grocery: Run desktop app** in VS Code. The desktop app uses Tkinter's macOS Aqua controls and the same inventory file as the console. Python must include Tkinter.

Select a product, enter a quantity and click **Add to Cart**. **Checkout** shows a confirmation and saves the updated stock. **Add Product** registers a product with its opening stock. Use **Command-F** to search and **Command-N** to add a product.

The desktop window covers grocery billing. The final project's expiry verification, stock receiving and waste reports are available through `python3 main.py --final-project`. When opening an inventory with dated batches, the window applies the same expiry eligibility rules.

## Assignment 2 submission material

The [user guide](docs/USER_GUIDE.md) includes a reproducible checkout demonstration and the screenshot checklist. [Recorded test results](docs/evidence/test-results.txt) and console transcripts are stored under docs/evidence.

Shared input validation lives in `grocery_system/validation.py`. Inventory loading also checks stored field types, ranges, unique IDs and references before accepting records.

The separate `Final Project/` folder is reserved for future work. The existing expiry and waste prototype remains here; no new final-project implementation has been added.
