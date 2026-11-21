"""Product, batch and discard records and the rules that change stock."""

from dataclasses import dataclass, field
from datetime import date

from .activity import Distribution
from .validation import validate_integer, validate_product


@dataclass
class Product:
    code: str
    name: str
    price_sen: int

    def __post_init__(self):
        validate_product(self.code, self.name, self.price_sen)


@dataclass
class Batch:
    # A batch is one delivery. Two deliveries of milk can expire on different days.
    batch_id: int
    product_code: str
    expiry: date | None
    quantity: int

    def __post_init__(self):
        validate_integer(self.batch_id, 1, "Batch ID")
        validate_integer(self.quantity)
        if self.expiry is not None and type(self.expiry) is not date:
            raise ValueError("Batch expiry must be a calendar date.")


@dataclass
class WasteEntry:
    product_code: str
    batch_id: int
    recorded_on: date
    reason: str
    quantity: int
    unit_price_sen: int

    def __post_init__(self):
        validate_integer(self.batch_id, 1, "Batch ID")
        validate_integer(self.quantity, 1)
        validate_integer(self.unit_price_sen, 1, "Price in sen")
        if self.unit_price_sen > 9999900:
            raise ValueError("Discard price exceeds the supported maximum.")
        if type(self.recorded_on) is not date:
            raise ValueError("Discard date must be a calendar date.")
        if self.reason not in ("Expired", "Damaged", "Other"):
            raise ValueError("Invalid discard reason.")


@dataclass
class Inventory:
    products: dict[str, Product] = field(default_factory=dict)
    batches: dict[int, Batch] = field(default_factory=dict)
    waste_entries: list[WasteEntry] = field(default_factory=list)

    distributions: list[Distribution] = field(default_factory=list)

    def add_product(self, code, name, price_sen):
        if code in self.products:
            raise ValueError("That product ID already exists.")
        self.products[code] = Product(code, name, price_sen)

    def receive_batch(self, code, quantity, expiry=None):
        """Create a delivery batch and return its unique ID."""
        if code not in self.products:
            raise ValueError("Invalid product ID.")
        validate_integer(quantity, 1)
        batch_id = max(self.batches, default=0) + 1
        self.batches[batch_id] = Batch(batch_id, code, expiry, quantity)
        return batch_id

    def assign_batch_expiry(self, batch_id, quantity, expiry):
        """Move verified units from undated stock into a dated batch."""
        if type(expiry) is not date:
            raise ValueError("Enter a verified calendar date.")
        batch = self.get_batch(batch_id)
        if batch.expiry is not None:
            raise ValueError("Choose a batch with an unverified expiry date.")
        self.validate_batch_quantity(batch, quantity)
        # A partial verification creates a dated batch for just those units.
        if quantity == batch.quantity:
            batch.expiry = expiry
            return batch_id

        dated_batch_id = self.receive_batch(batch.product_code, quantity, expiry)
        batch.quantity -= quantity
        return dated_batch_id

    def sellable_batches(self, code, today, track_expiry):
        available = []
        for batch in self.batches.values():
            if batch.product_code != code or batch.quantity <= 0:
                continue
            if batch.expiry is None:
                if not track_expiry:
                    available.append(batch)
            elif batch.expiry >= today:
                available.append(batch)
        # Sell the earliest expiry first; batch ID breaks ties.
        return sorted(available, key=lambda batch: (batch.expiry or date.max, batch.batch_id))

    def available_quantity(self, code, today, track_expiry):
        return sum(batch.quantity for batch in self.sellable_batches(code, today, track_expiry))

    def checkout(self, cart, today, track_expiry):
        """Validate the whole cart before applying earliest-expiry allocations."""
        # Plan every allocation before deducting stock from any batch.
        allocations = []
        for code, quantity in cart.items():
            validate_integer(quantity, 1)
            batches = self.sellable_batches(code, today, track_expiry)
            if quantity <= 0 or quantity > sum(batch.quantity for batch in batches):
                raise ValueError(f"Insufficient sellable stock for product {code}. Review the cart.")
            remaining = quantity
            for batch in batches:
                used = min(batch.quantity, remaining)
                allocations.append((batch, used))
                remaining -= used
                if remaining == 0:
                    break

        for batch, used in allocations:
            self.distributions.append(Distribution(batch.batch_id, used, today, self.products[batch.product_code].price_sen))
            batch.quantity -= used
        return [(batch.batch_id, used) for batch, used in allocations]

    def donate(self, batch_id, quantity, recipient, today):
        batch = self.get_batch(batch_id)
        self.validate_batch_quantity(batch, quantity)
        if batch.expiry is None or batch.expiry < today:
            raise ValueError("Choose a batch with a verified expiry of today or later.")
        entry = Distribution(batch_id, quantity, today, self.products[batch.product_code].price_sen,
                             recipient.strip())
        self.distributions.append(entry)
        batch.quantity -= quantity

    def expiry_alerts(self, today, days=7):
        alerts = []
        for batch in self.batches.values():
            if batch.quantity > 0 and batch.expiry is not None:
                if (batch.expiry - today).days <= days:
                    alerts.append(batch)
        return sorted(alerts, key=lambda batch: (batch.expiry, batch.batch_id))

    def get_batch(self, batch_id):
        if batch_id not in self.batches:
            raise ValueError("Batch ID not found.")
        return self.batches[batch_id]

    def validate_batch_quantity(self, batch, quantity):
        validate_integer(quantity, 1)
        if quantity <= 0 or quantity > batch.quantity:
            raise ValueError("Quantity must be positive and within the batch stock.")

    def record_waste(self, batch_id, quantity, reason, today):
        batch = self.get_batch(batch_id)
        self.validate_batch_quantity(batch, quantity)
        if reason == "Expired" and (batch.expiry is None or batch.expiry >= today):
            raise ValueError("Expired discards require a verified date before today.")
        product = self.products[batch.product_code]
        # Keep the current price in history even if the product price changes.
        self.waste_entries.append(
            WasteEntry(product.code, batch_id, today, reason, quantity, product.price_sen)
        )
        batch.quantity -= quantity

    def waste_summary(self):
        """Group discarded units and recorded retail value by product and reason."""
        totals = {}
        for entry in self.waste_entries:
            key = (entry.product_code, entry.reason)
            units, value = totals.get(key, (0, 0))
            totals[key] = (units + entry.quantity, value + entry.quantity * entry.unit_price_sen)
        return totals
