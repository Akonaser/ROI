"""The batch review window for Smart Grocery."""
from collections import Counter
from copy import deepcopy
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

from grocery_system.storage import save_inventory
from grocery_system.validation import format_display_date, parse_display_date, parse_quantity


class StockWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app.root)
        self.app = app
        self.title("Stock batches")
        self.transient(app.root)
        self.grab_set()
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        self.alerts = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Only expired, due within 7 days, or undated",
                        variable=self.alerts, command=self.refresh).pack(anchor="w")
        self.table = app.make_table(frame, [
            ("name", "Product", 180), ("id", "Batch", 60), ("qty", "Units", 65),
            ("expiry", "Expiry", 110), ("status", "Status", 125)])

        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=(10, 0))
        for label in ("Receive", "Verify expiry", "Donate", "Record waste"):
            ttk.Button(actions, text=label, command=lambda action=label: self.form(action)).pack(side="left")
        self.refresh()

    def refresh(self):
        self.table.delete(*self.table.get_children())
        today = date.today()
        batches = sorted(self.app.inventory.batches.values(), key=lambda b: (b.expiry or date.max, b.batch_id))
        for batch in batches:
            if not batch.quantity:
                continue
            days = (batch.expiry - today).days if batch.expiry else None
            if days is None:
                status = "Verify date"
            elif days < 0:
                status = "Expired"
            elif days == 0:
                status = "Due today"
            elif days <= 7:
                status = f"Due in {days} days"
            else:
                if self.alerts.get():
                    continue
                status = "In date"
            product = self.app.inventory.products[batch.product_code]
            self.table.insert("", "end", iid=str(batch.batch_id), values=(
                product.name, batch.batch_id, batch.quantity, format_display_date(batch.expiry) if batch.expiry else "—", status))

    def form(self, action):
        selected = self.table.selection()
        inventory = self.app.inventory
        if action == "Receive" and not inventory.products:
            messagebox.showinfo(action, "Add a product first.", parent=self)
            return
        if action != "Receive" and not selected:
            messagebox.showinfo(action, "Select a batch first.", parent=self)
            return
        batch = inventory.get_batch(int(selected[0])) if selected else None
        dialog = tk.Toplevel(self)
        dialog.title(action)
        dialog.transient(self)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)
        if action == "Receive":
            products = list(inventory.products.values())
            # Names stay uncluttered unless two products need distinguishing.
            counts = Counter(item.name.casefold() for item in products)
            labels = [
                item.name if counts[item.name.casefold()] == 1 else f"{item.name} (ID {item.code})"
                for item in products
            ]
            ttk.Label(frame, text="Product").pack(anchor="w")
            product = ttk.Combobox(frame, values=labels, state="readonly")
            # Receiving from a highlighted batch should default to its product.
            initial = inventory.products[batch.product_code] if batch else products[0]
            product.current(products.index(initial))
            product.pack(fill="x")
        else:
            name = inventory.products[batch.product_code].name
            ttk.Label(frame, text=f"{name} · Batch #{batch.batch_id} · {batch.quantity} units").pack(anchor="w")
        ttk.Label(frame, text="Quantity").pack(anchor="w", pady=(10, 2))
        quantity = ttk.Entry(frame)
        quantity.insert(0, "1")
        quantity.pack(fill="x")
        label = {"Receive": "Expiry (DD MM YYYY)", "Verify expiry": "Verified expiry (DD MM YYYY)",
                 "Donate": "Recipient or organisation", "Record waste": "Reason"}[action]
        ttk.Label(frame, text=label).pack(anchor="w", pady=(10, 2))
        if action == "Record waste":
            detail = ttk.Combobox(frame, values=("Expired", "Damaged", "Other"), state="readonly")
            detail.current(0)
        else:
            detail = ttk.Entry(frame)
        detail.pack(fill="x")
        error = tk.StringVar()
        ttk.Label(frame, textvariable=error, wraplength=320).pack()

        def close():
            dialog.destroy()
            self.grab_set()

        def save():
            # Publish the edited stock only after the entire file saves successfully.
            updated = deepcopy(self.app.inventory)
            try:
                units = parse_quantity(quantity.get())
                value = detail.get().strip()
                today = date.today()
                if action == "Receive":
                    updated.receive_batch(products[product.current()].code, units, parse_display_date(value))
                elif action == "Verify expiry":
                    updated.assign_batch_expiry(batch.batch_id, units, parse_display_date(value))
                elif action == "Donate":
                    updated.donate(batch.batch_id, units, value, today)
                else:
                    updated.record_waste(batch.batch_id, units, value, today)
                save_inventory(self.app.data_path, updated)
            except (ValueError, OSError) as exc:
                error.set(str(exc))
                return
            self.app.inventory = updated
            self.app.refresh()
            self.refresh()
            self.app.status.set(f"{action} saved · {units} unit(s).")
            close()

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Cancel", command=close).pack(side="left")
        ttk.Button(buttons, text=f"Confirm {action.lower()}", command=save).pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", close)
        dialog.bind("<Escape>", lambda _: close())
        quantity.focus_set()
