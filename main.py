"""Run the Assignment 2 or course final project console."""

import argparse
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import grocery
from grocery_system.inventory import Inventory
from grocery_system.storage import load_inventory


def starter_inventory():
    inventory = Inventory()
    # Preserve the original catalogue and its opening stock.
    for code, name, price_sen, stock in [
        ("1", "Rice", 1500, 20),
        ("2", "Milk", 750, 15),
        ("3", "Bread", 400, 25),
        ("4", "Eggs", 1200, 18),
        ("5", "Cooking Oil", 950, 12),
    ]:
        inventory.add_product(code, name, price_sen)
        inventory.receive_batch(code, stock)
    return inventory


def demo_inventory(today):
    inventory = Inventory()
    inventory.add_product("2", "Milk", 750)
    inventory.add_product("6", "Yogurt", 250)
    inventory.receive_batch("2", 5, today + timedelta(days=2))
    inventory.receive_batch("2", 15, today + timedelta(days=12))
    inventory.receive_batch("6", 4, today - timedelta(days=1))
    return inventory


def display_menu(track_expiry):
    title = "SMART GROCERY & FOOD WASTE MANAGEMENT" if track_expiry else "SMART GROCERY BILLING"
    print(f"\n========== {title} ==========")
    print("1. View products and stock\n2. Register product\n3. Add to cart")
    print("4. View cart\n5. Generate bill and checkout\n6. Clear cart")
    if track_expiry:
        print("7. Receive stock\n8. Check expiry alerts\n9. Record food waste")
        print("10. View waste report\n11. Verify expiry of existing stock")
    print("0. Exit")


def run_menu(inventory, track_expiry, path):
    cart = {}
    while True:
        display_menu(track_expiry)
        choice = input("Choose an option: ").strip()
        today = date.today()
        try:
            if choice == "1":
                grocery.show_inventory(inventory, today, track_expiry)
            elif choice == "2":
                grocery.register_product(inventory, track_expiry, path)
            elif choice == "3":
                grocery.add_to_cart(inventory, cart, today, track_expiry)
            elif choice == "4":
                grocery.view_cart(inventory, cart)
            elif choice == "5":
                grocery.generate_bill(inventory, cart, track_expiry, path)
            elif choice == "6":
                cart.clear()
                print("Cart cleared.")
            elif choice == "7" and track_expiry:
                grocery.receive_stock(inventory, path)
            elif choice == "8" and track_expiry:
                grocery.show_expiry_alerts(inventory, today)
            elif choice == "9" and track_expiry:
                grocery.record_discard(inventory, path)
            elif choice == "10" and track_expiry:
                grocery.show_waste_report(inventory)
            elif choice == "11" and track_expiry:
                grocery.verify_expiry(inventory, path)
            elif choice == "0":
                print("Goodbye.")
                break
            else:
                print("Choose one of the listed options.")
        except ValueError as error:
            print(f"Input error: {error}")


def main():
    parser = argparse.ArgumentParser(description="Smart Grocery Management System")
    parser.add_argument("--final-project", action="store_true", help="enable expiry and waste tools")
    parser.add_argument("--demo", action="store_true", help="run the final project with temporary sample stock")
    parser.add_argument("--data", type=Path, default=Path("inventory.json"), help="path to the inventory file")
    args = parser.parse_args()
    try:
        if args.demo:
            with TemporaryDirectory() as folder:
                print("Demo mode. Sample stock resets when you exit.")
                run_menu(demo_inventory(date.today()), True, Path(folder) / "inventory.json")
            return

        try:
            inventory = load_inventory(args.data)
        except FileNotFoundError:
            inventory = Inventory() if args.final_project else starter_inventory()

        if not args.final_project and any(batch.expiry is not None for batch in inventory.batches.values()):
            parser.exit(1, "This inventory contains dated batches. Run with --final-project.\n")

        run_menu(inventory, args.final_project, args.data)
    except (EOFError, KeyboardInterrupt):
        print("\nSession closed.")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Unable to continue with the inventory file: {error}\n")


if __name__ == "__main__":
    main()
