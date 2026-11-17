"""Console functions for the grocery catalogue, cart, billing and waste reports."""

from datetime import date

from grocery_system.storage import save_inventory
from grocery_system.validation import parse_quantity, parse_price, parse_date


def format_money(sen):
    # Store money in sen; split it into ringgit and sen for display.
    return f"{sen // 100:,}.{sen % 100:02d}"


def read_whole_number(prompt, minimum=1):
    """Read and validate a quantity using the shared input rules."""
    return parse_quantity(input(prompt), minimum)


def read_price():
    """Read an RM amount and return its value in integer sen."""
    return parse_price(input("Unit price (RM): "))


def read_expiry():
    """Read a verified calendar date for a stock batch."""
    return parse_date(input("Expiry date (YYYY-MM-DD): ").strip())


def display_products(inventory, today, track_expiry):
    print("\n========== AVAILABLE PRODUCTS ==========")
    print(f"{'ID':<7}{'Product':<25}{'Price (RM)':<15}{'Sellable units'}")
    for product_id, product in inventory.products.items():
        stock = inventory.available_quantity(product_id, today, track_expiry)
        print(f"{product_id:<7}{product.name:<25}{format_money(product.price_sen):<15}{stock}")


def register_product(inventory, track_expiry, path):
    code = input("New product ID (1-6 letters or digits): ").strip().upper()
    if code in inventory.products:
        raise ValueError("That product ID already exists.")
    name = input("Product name: ").strip()
    price_sen = read_price()
    stock = 0
    if not track_expiry:
        stock = read_whole_number("Opening stock: ", minimum=0)
    inventory.add_product(code, name, price_sen)
    if stock:
        inventory.receive_batch(code, stock)
    save_inventory(path, inventory)
    print("Product registered.")


def add_to_cart(inventory, cart, today, track_expiry):
    display_products(inventory, today, track_expiry)
    product_id = input("\nEnter product ID: ").strip().upper()
    if product_id not in inventory.products:
        raise ValueError("Invalid product ID.")
    quantity = read_whole_number("Enter quantity: ")
    # Include units already in the cart when checking available stock.
    requested = cart.get(product_id, 0) + quantity
    if requested > inventory.available_quantity(product_id, today, track_expiry):
        raise ValueError("Your cart quantity exceeds the available stock.")
    cart[product_id] = requested
    print("Product added to cart successfully.")


def calculate_bill(inventory, cart):
    """Return itemised lines and the total in sen without changing stock."""
    lines = []
    for product_id, quantity in cart.items():
        product = inventory.products[product_id]
        subtotal = product.price_sen * quantity
        lines.append((product.name, quantity, product.price_sen, subtotal))
    return lines, sum(line[3] for line in lines)


def view_cart(inventory, cart):
    print("\n========== SHOPPING CART ==========")
    if not cart:
        print("Your cart is empty.")
        return
    print_bill(inventory, cart)


def print_bill(inventory, cart):
    lines, total = calculate_bill(inventory, cart)
    print(f"{'Product':<25}{'Qty':>5}{'Unit (RM)':>13}{'Subtotal (RM)':>16}")
    for name, quantity, price, subtotal in lines:
        print(f"{name:<25}{quantity:>5}{format_money(price):>13}{format_money(subtotal):>16}")
    print(f"Total: RM {format_money(total)}")


def generate_bill(inventory, cart, track_expiry, path):
    """Confirm the sale, deduct validated quantities and persist stock."""
    if not cart:
        print("Your cart is empty. Add products first.")
        return
    print("\n========== FINAL BILL ==========")
    print_bill(inventory, cart)
    if input("Confirm purchase? (y/n): ").strip().lower() != "y":
        print("Purchase cancelled. Your cart is still available.")
        return

    allocations = inventory.checkout(cart, date.today(), track_expiry)
    save_inventory(path, inventory)
    cart.clear()
    if track_expiry:
        for batch_id, quantity in allocations:
            print(f"Batch #{batch_id}: {quantity} unit(s) sold")
    print("Purchase saved. Stock updated.")


def print_batches(inventory, batches, today):
    print(f"{'Batch':<7}{'Product':<25}{'Qty':>5}  {'Expiry':<12}Status")
    for batch in batches:
        product = inventory.products[batch.product_code]
        if batch.expiry is None:
            expiry, status = "-", "Verify expiry before sale"
        else:
            expiry = batch.expiry.isoformat()
            days_left = (batch.expiry - today).days
            if days_left < 0:
                status = "Expired"
            elif days_left == 0:
                status = "Expires today"
            elif days_left <= 7:
                status = f"Due in {days_left} day(s)"
            else:
                status = "Outside alert window"
        print(f"{batch.batch_id:<7}{product.name:<25}{batch.quantity:>5}  {expiry:<12}{status}")


def show_inventory(inventory, today, track_expiry):
    display_products(inventory, today, track_expiry)
    if track_expiry:
        batches = [batch for batch in inventory.batches.values() if batch.quantity > 0]
        if batches:
            print()
            print_batches(inventory, batches, today)


def receive_stock(inventory, path):
    code = input("Product ID: ").strip().upper()
    expiry = read_expiry()
    quantity = read_whole_number("Units received: ")
    batch_id = inventory.receive_batch(code, quantity, expiry)
    save_inventory(path, inventory)
    print(f"Saved batch #{batch_id}.")


def verify_expiry(inventory, path):
    batch_id = read_whole_number("Undated batch ID: ")
    quantity = read_whole_number("Units with this expiry date: ")
    expiry = read_expiry()
    dated_batch_id = inventory.assign_batch_expiry(batch_id, quantity, expiry)
    save_inventory(path, inventory)
    print(f"Saved verified expiry date for batch #{dated_batch_id}.")


def show_expiry_alerts(inventory, today):
    alerts = inventory.expiry_alerts(today)
    if alerts:
        print_batches(inventory, alerts, today)
        if any(batch.expiry < today for batch in alerts):
            print("Review expired batches for removal and record confirmed discards.")
        if any(batch.expiry >= today for batch in alerts):
            print("Review near-expiry stock and rotate the earliest dates to the front.")
    else:
        print("No stocked batches are expired or due within 7 days.")
    if any(batch.expiry is None and batch.quantity > 0 for batch in inventory.batches.values()):
        print("Some stock has unverified expiry dates. See the inventory list to find those batches.")


def record_discard(inventory, path):
    batch_id = read_whole_number("Batch ID: ")
    quantity = read_whole_number("Units discarded: ")
    reasons = {"1": "Expired", "2": "Damaged", "3": "Other"}
    choice = input("Reason (1. Expired, 2. Damaged, 3. Other): ").strip()
    if choice not in reasons:
        raise ValueError("Choose reason 1, 2 or 3.")
    inventory.record_waste(batch_id, quantity, reasons[choice], date.today())
    save_inventory(path, inventory)
    print("Waste recorded. Batch stock updated.")


def show_waste_report(inventory):
    totals = inventory.waste_summary()
    if not totals:
        print("No food waste has been recorded.")
        return
    print("Recorded waste by product and reason")
    print(f"{'Product':<25}{'Reason':<12}{'Units':>6}{'Value (RM)':>15}")
    for (code, reason), (units, value) in sorted(totals.items()):
        print(f"{inventory.products[code].name:<25}{reason:<12}{units:>6}{format_money(value):>15}")
    print(f"Total discarded units: {sum(units for units, _ in totals.values())}")
    print(f"Estimated retail value: RM {format_money(sum(value for _, value in totals.values()))}")
    print("Review repeatedly discarded products before placing the next order.")
