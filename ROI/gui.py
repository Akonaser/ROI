"""Run the grocery billing desktop interface with python3 gui.py."""

import argparse
from copy import deepcopy
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from grocery import calculate_bill, format_money
from grocery_system.storage import load_inventory, save_inventory
from grocery_system.validation import parse_quantity, parse_price, parse_date
from main import starter_inventory


class GroceryApp:
    """A desktop view over the same inventory and cart used by the console."""

    def __init__(self, root, inventory, data_path):
        self.root = root
        self.inventory = inventory
        self.data_path = data_path
        self.cart = {}
        self.track_expiry = any(batch.expiry is not None for batch in inventory.batches.values())
        self.quantity = tk.StringVar(value="1")
        self.total = tk.StringVar(value="RM 0.00")
        self.status = tk.StringVar(value="Select a product and enter a quantity to start a sale.")
        self.search = tk.StringVar()
        self.product_dialog = None

        root.title("Smart Grocery")
        root.geometry("1020x640")
        root.minsize(840, 520)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Command-q>", lambda event: self.close())
        root.bind("<Command-n>", lambda event: self.open_product_dialog())
        root.bind("<Command-f>", self.focus_search)

        style = ttk.Style(root)
        # Aqua supplies macOS controls and follows the system appearance.
        if "aqua" in style.theme_names():
            style.theme_use("aqua")
        style.configure("Treeview", rowheight=29)
        style.configure("Title.TLabel", font=("TkDefaultFont", 22, "bold"))
        style.configure("Total.TLabel", font=("TkDefaultFont", 20, "bold"))

        page = ttk.Frame(root, padding=22)
        page.pack(fill="both", expand=True)
        header = ttk.Frame(page)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(header, text="Smart Grocery", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Add Product", command=self.open_product_dialog).pack(side="right")

        content = ttk.Frame(page)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        catalogue = ttk.LabelFrame(content, text="Products", padding=12)
        catalogue.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ttk.Label(catalogue, text="Search products").pack(anchor="w")
        self.search_entry = ttk.Entry(catalogue, textvariable=self.search)
        self.search_entry.pack(fill="x", pady=(4, 10))
        self.search.trace_add("write", lambda *_: self.refresh_products())
        self.products_table = self.make_table(catalogue, [
            ("name", "Product", 185), ("price", "Price (RM)", 95), ("stock", "Available", 80),
        ])
        self.products_table.bind("<Double-1>", lambda event: self.add_selected())
        self.products_table.bind("<Return>", lambda event: self.add_selected())
        entry_row = ttk.Frame(catalogue)
        entry_row.pack(fill="x", pady=(12, 0))
        ttk.Label(entry_row, text="Quantity").pack(side="left")
        self.quantity_entry = ttk.Entry(entry_row, textvariable=self.quantity, width=7)
        self.quantity_entry.pack(side="left", padx=8)
        self.quantity_entry.bind("<Return>", lambda event: self.add_selected())
        ttk.Button(entry_row, text="Add to Cart", command=self.add_selected).pack(side="right")

        cart_panel = ttk.LabelFrame(content, text="Current sale", padding=12)
        cart_panel.grid(row=0, column=1, sticky="nsew")
        self.cart_table = self.make_table(cart_panel, [
            ("name", "Product", 150), ("quantity", "Qty", 45), ("amount", "Amount (RM)", 105),
        ])
        actions = ttk.Frame(cart_panel)
        actions.pack(fill="x", pady=10)
        ttk.Button(actions, text="Remove Item", command=self.remove_selected).pack(side="left")
        ttk.Button(actions, text="Clear Cart", command=self.clear_cart).pack(side="right")
        ttk.Separator(cart_panel).pack(fill="x", pady=8)
        summary = ttk.Frame(cart_panel)
        summary.pack(fill="x", pady=(8, 12))
        ttk.Label(summary, text="Total").pack(side="left")
        ttk.Label(summary, textvariable=self.total, style="Total.TLabel").pack(side="right")
        self.checkout_button = ttk.Button(cart_panel, text="Checkout", command=self.checkout)
        self.checkout_button.pack(fill="x")
        ttk.Label(page, textvariable=self.status, wraplength=940).pack(fill="x", pady=(16, 0))
        self.refresh()

    def make_table(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        table = ttk.Treeview(frame, columns=[column[0] for column in columns],
                             show="headings", selectmode="browse", height=10)
        for index, (name, heading, width) in enumerate(columns):
            table.heading(name, text=heading)
            table.column(name, width=width, minwidth=45,
                         anchor="w" if index == 0 else "e", stretch=index == 0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        table.pack(side="left", fill="both", expand=True)
        return table

    def focus_search(self, event=None):
        self.search_entry.focus_set()
        self.search_entry.selection_range(0, "end")
        return "break"

    def refresh_products(self):
        selected = self.products_table.selection()
        for item in self.products_table.get_children():
            self.products_table.delete(item)
        # Match product names and IDs without case sensitivity.
        query = self.search.get().strip().casefold()
        for code, product in self.inventory.products.items():
            if query and query not in product.name.casefold() and query not in code.casefold():
                continue
            available = self.inventory.available_quantity(code, date.today(), self.track_expiry)
            self.products_table.insert("", "end", iid=code, values=(
                product.name, format_money(product.price_sen), available,
            ))
        if selected and self.products_table.exists(selected[0]):
            self.products_table.selection_set(selected[0])

    def refresh(self):
        self.refresh_products()
        for item in self.cart_table.get_children():
            self.cart_table.delete(item)
        for code, quantity in self.cart.items():
            product = self.inventory.products[code]
            self.cart_table.insert("", "end", iid=code, values=(
                product.name, quantity, format_money(product.price_sen * quantity),
            ))
        _, total = calculate_bill(self.inventory, self.cart)
        self.total.set(f"RM {format_money(total)}")
        # Checkout is available only when the cart contains items.
        self.checkout_button.configure(state="normal" if self.cart else "disabled")

    def add_selected(self):
        selected = self.products_table.selection()
        if not selected:
            self.status.set("Select a product first.")
            return
        code = selected[0]
        try:
            quantity = parse_quantity(self.quantity.get())
        except ValueError:
            self.status.set("Enter a positive whole number for quantity.")
            self.quantity_entry.focus_set()
            return
        requested = self.cart.get(code, 0) + quantity
        available = self.inventory.available_quantity(code, date.today(), self.track_expiry)
        if requested > available:
            self.status.set(f"Only {available} units are available. Your cart already contains {self.cart.get(code, 0)}.")
            return
        self.cart[code] = requested
        self.refresh()
        self.status.set(f"Added {quantity} × {self.inventory.products[code].name} to the cart.")

    def remove_selected(self):
        selected = self.cart_table.selection()
        if not selected:
            self.status.set("Select an item in the cart to remove.")
            return
        del self.cart[selected[0]]
        self.refresh()
        self.status.set("Item removed from the cart.")

    def clear_cart(self):
        self.cart.clear()
        self.refresh()
        self.status.set("Cart cleared.")

    def checkout(self):
        if not self.cart:
            return
        _, total = calculate_bill(self.inventory, self.cart)
        if not messagebox.askyesno("Confirm purchase", f"Complete this sale for RM {format_money(total)}?",
                                   parent=self.root):
            return
        # Save a candidate inventory before replacing the visible state.
        updated = deepcopy(self.inventory)
        try:
            updated.checkout(self.cart, date.today(), self.track_expiry)
            save_inventory(self.data_path, updated)
        except (ValueError, OSError) as error:
            messagebox.showerror("Purchase could not be saved", str(error), parent=self.root)
            return
        self.inventory = updated
        self.cart.clear()
        self.refresh()
        self.status.set(f"Sale completed for RM {format_money(total)}. Stock saved.")

    def open_product_dialog(self):
        if self.product_dialog and self.product_dialog.winfo_exists():
            self.product_dialog.lift()
            return
        dialog = tk.Toplevel(self.root)
        self.product_dialog = dialog
        dialog.title("Add Product")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        frame = ttk.Frame(dialog, padding=22)
        frame.pack(fill="both", expand=True)
        fields = {}
        definitions = [
            ("code", "Product ID", ""), ("name", "Product name", ""),
            ("price", "Unit price (RM)", ""), ("stock", "Opening stock", "0"),
        ]
        if self.track_expiry:
            definitions.append(("expiry", "Expiry date (YYYY-MM-DD)", ""))
        for row, (key, label, default) in enumerate(definitions):
            ttk.Label(frame, text=label).grid(row=row * 2, column=0, sticky="w", pady=(8, 3))
            fields[key] = ttk.Entry(frame, width=37)
            fields[key].insert(0, default)
            fields[key].grid(row=row * 2 + 1, column=0, sticky="ew")
        error_text = tk.StringVar()
        ttk.Label(frame, textvariable=error_text, wraplength=310).grid(row=10, column=0, pady=12)
        ttk.Button(frame, text="Save Product",
                   command=lambda: self.save_product(fields, dialog, error_text)).grid(row=11, column=0, sticky="e")
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        fields["code"].focus_set()
        dialog.grab_set()

    def save_product(self, fields, dialog, error_text):
        try:
            code = fields["code"].get().strip().upper()
            name = fields["name"].get().strip()
            price_sen = parse_price(fields["price"].get())
            stock = parse_quantity(fields["stock"].get(), minimum=0)
            expiry_text = fields["expiry"].get().strip() if "expiry" in fields else ""
            expiry = parse_date(expiry_text) if expiry_text else None
            if self.track_expiry and stock and expiry is None:
                raise ValueError("Enter an expiry date for stock in this dated inventory.")
            updated = deepcopy(self.inventory)
            updated.add_product(code, name, price_sen)
            if stock:
                updated.receive_batch(code, stock, expiry)
            save_inventory(self.data_path, updated)
        except (ValueError, OSError) as error:
            error_text.set(str(error))
            return
        self.inventory = updated
        self.track_expiry = any(batch.expiry is not None for batch in updated.batches.values())
        self.refresh()
        self.status.set(f"Added {name}. Product and stock saved.")
        dialog.destroy()

    def close(self):
        if self.cart and not messagebox.askyesno(
            "Close Smart Grocery", "Discard the current cart and close?", parent=self.root
        ):
            return
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="Smart Grocery desktop interface")
    parser.add_argument("--data", type=Path, default=Path("inventory.json"))
    args = parser.parse_args()
    root = tk.Tk()
    root.withdraw()
    try:
        try:
            inventory = load_inventory(args.data)
        except FileNotFoundError:
            inventory = starter_inventory()
        GroceryApp(root, inventory, args.data)
    except (OSError, ValueError, TypeError, KeyError) as error:
        messagebox.showerror("Inventory could not be opened", str(error), parent=root)
        root.destroy()
        return
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
