
# Product catalogue
products = {
    "1": {"name": "Rice", "price": 15.00, "stock": 20},
    "2": {"name": "Milk", "price": 7.50, "stock": 15},
    "3": {"name": "Bread", "price": 4.00, "stock": 25},
    "4": {"name": "Eggs", "price": 12.00, "stock": 18},
    "5": {"name": "Cooking Oil", "price": 9.50, "stock": 12}
}


# Display all available products
def display_products():
    print("\n========== AVAILABLE PRODUCTS ==========")
    print(f"{'ID':<5}{'Product':<20}{'Price (RM)':<15}{'Stock'}")

    for product_id, details in products.items():
        print(
            f"{product_id:<5}"
            f"{details['name']:<20}"
            f"{details['price']:<15.2f}"
            f"{details['stock']}"
        )


# Add a product to the shopping cart
def add_to_cart(cart):
    display_products()

    product_id = input("\nEnter product ID: ")

    if product_id not in products:
        print("Invalid product ID.")
        return

    try:
        quantity = int(input("Enter quantity: "))

        if quantity <= 0:
            print("Quantity must be greater than zero.")
        elif quantity > products[product_id]["stock"]:
            print("Not enough stock available.")
        else:
            current_quantity = cart.get(product_id, 0)

            if current_quantity + quantity > products[product_id]["stock"]:
                print("Your cart quantity exceeds the available stock.")
            else:
                cart[product_id] = current_quantity + quantity
                print("Product added to cart successfully.")

    except ValueError:
        print("Please enter a valid whole number.")


# Display shopping cart
def view_cart(cart):
    print("\n========== SHOPPING CART ==========")

    if not cart:
        print("Your cart is empty.")
        return

    total = 0

    for product_id, quantity in cart.items():
        product = products[product_id]
        subtotal = product["price"] * quantity
        total += subtotal

        print(
            f"{product['name']} x {quantity} "
            f"= RM {subtotal:.2f}"
        )

    print("-----------------------------------")
    print(f"Total: RM {total:.2f}")


# Generate the final bill
def generate_bill(cart):
    if not cart:
        print("\nYour cart is empty. Add products first.")
        return

    print("\n========== FINAL BILL ==========")

    total = 0

    for product_id, quantity in cart.items():
        product = products[product_id]
        subtotal = product["price"] * quantity
        total += subtotal

        print(
            f"{product['name']} x {quantity} "
            f"= RM {subtotal:.2f}"
        )

    print("--------------------------------")
    print(f"TOTAL PAYMENT: RM {total:.2f}")
    print("Thank you for shopping!")

    # Update product stock after purchase
    for product_id, quantity in cart.items():
        products[product_id]["stock"] -= quantity

    cart.clear()

