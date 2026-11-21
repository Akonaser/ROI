"""Run the food surplus console."""

import argparse
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import grocery
from grocery_system.inventory import Inventory
from grocery_system.storage import load_inventory, inventory_session


def demo_inventory(today):
    """Replay a week of sample activity relative to the day the demo opens."""
    inventory = Inventory()
    catalogue = [
        ("2", "Milk", 750), ("6", "Yogurt", 250), ("BR", "Wholemeal Bread", 420),
        ("EG", "Eggs (10 pack)", 680), ("RC", "Rice (5 kg)", 1890),
        ("TF", "Firm Tofu", 320), ("BN", "Bananas (bunch)", 490),
        ("TM", "Canned Tomatoes", 580), ("OT", "Rolled Oats", 890),
        ("ND", "Rice Noodles", 360), ("SP", "Spinach (bag)", 350),
        ("AP", "Apples (4 pack)", 690),
    ]

    for code, name, price_sen in catalogue:
        inventory.add_product(code, name, price_sen)

    def delivery(code, units, days_to_expiry):
        expiry = today + timedelta(days=days_to_expiry) if days_to_expiry is not None else None
        return inventory.receive_batch(code, units, expiry)

    # Separate deliveries of one product can have different expiry dates.
    delivery("2", 14, 2)
    delivery("2", 15, 12)
    old_yogurt = delivery("6", 12, -2)
    delivery("6", 16, 9)
    bread = delivery("BR", 20, 0)
    delivery("EG", 15, 14)
    delivery("RC", 18, 150)
    tofu = delivery("TF", 14, 3)
    bananas = delivery("BN", 16, 1)
    delivery("TM", 24, 240)
    delivery("OT", 12, 120)
    delivery("ND", 15, 90)
    delivery("SP", 8, None)  # Staff must verify the label before distributing these bags.
    delivery("AP", 12, 8)

    # Replay transactions through the same rules as checkout and the batch window.
    for days_ago, cart in [
        (6, {"2": 4, "6": 5, "RC": 2}),
        (4, {"BR": 5, "EG": 3, "TM": 4}),
        (2, {"2": 5, "TF": 3, "AP": 4}),
        (1, {"BR": 3, "OT": 2, "ND": 3}),
    ]:
        inventory.checkout(cart, today - timedelta(days=days_ago), True)
    inventory.donate(bread, 4, "Campus Pantry", today - timedelta(days=1))
    inventory.donate(tofu, 3, "Community Kitchen", today)
    inventory.record_waste(old_yogurt, 3, "Expired", today - timedelta(days=1))
    inventory.record_waste(bananas, 2, "Damaged", today)
    return inventory


def display_menu():
    print("\n========== SMART GROCERY · FOOD SURPLUS ==========")
    print("1. View stock              7. Receive stock")
    print("2. Register product        8. Check expiry alerts")
    print("3. Add to cart             9. Record food waste")
    print("4. View cart              10. View waste report")
    print("5. Checkout               11. Verify undated stock")
    print("6. Clear cart             12. Record donation")
    print("                          13. Stock and distribution report")
    print("0. Exit")


def run_menu(inventory, path):
    # The cart lasts for this session; confirmed stock changes are saved.
    cart = {}
    while True:
        display_menu()
        choice = input("Choose an option: ").strip()
        today = date.today()
        try:
            if choice == "1":
                grocery.show_inventory(inventory, today, True)
            elif choice == "2":
                grocery.register_product(inventory, True, path)
            elif choice == "3":
                grocery.add_to_cart(inventory, cart, today, True)
            elif choice == "4":
                grocery.view_cart(inventory, cart)
            elif choice == "5":
                grocery.generate_bill(inventory, cart, True, path)
            elif choice == "6":
                cart.clear()
                print("Cart cleared.")
            elif choice == "7":
                grocery.receive_stock(inventory, path)
            elif choice == "8":
                grocery.show_expiry_alerts(inventory, today)
            elif choice == "9":
                grocery.record_discard(inventory, path)
            elif choice == "10":
                grocery.show_waste_report(inventory)
            elif choice == "11":
                grocery.verify_expiry(inventory, path)
            elif choice == "12":
                grocery.record_donation(inventory, path)
            elif choice == "13":
                print(grocery.activity_report(inventory))
            elif choice == "0":
                print("Goodbye.")
                break
            else:
                print("Choose one of the listed options.")
        except ValueError as error:
            print(f"Input error: {error}")


def main():
    parser = argparse.ArgumentParser(description="Smart Grocery Management System")

    parser.add_argument("--demo", action="store_true", help="run the final project with temporary sample stock")
    parser.add_argument("--data", type=Path, default=Path(__file__).with_name("surplus.json"), help="path to the inventory file")
    args = parser.parse_args()
    try:
        # Demo stock uses a temporary file so real inventory stays untouched.
        if args.demo:
            with TemporaryDirectory() as folder:
                print("Demo mode. Sample stock resets when you exit.")
                run_menu(demo_inventory(date.today()), Path(folder) / "inventory.json")
            return

        with inventory_session(args.data):
            try:
                inventory = load_inventory(args.data)
            except FileNotFoundError:
                inventory = Inventory()

            run_menu(inventory, args.data)
    except (EOFError, KeyboardInterrupt):
        print("\nSession closed.")
    except (OSError, ValueError) as error:
        parser.exit(1, f"Unable to continue with the inventory file: {error}\n")


if __name__ == "__main__":
    main()
