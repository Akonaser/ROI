"""Confirmed food distributions and their retail values."""
from dataclasses import dataclass
from datetime import date

from .validation import validate_integer


@dataclass
class Distribution:
    batch_id: int
    quantity: int
    recorded_on: date
    unit_price_sen: int
    recipient: str | None = None  # Sales have no donation recipient.

    def __post_init__(self):
        validate_integer(self.batch_id, 1, "Batch ID")
        validate_integer(self.quantity, 1)
        validate_integer(self.unit_price_sen, 1, "Price in sen")
        if type(self.recorded_on) is not date:
            raise ValueError("Invalid distribution date.")
        if self.recipient is not None and not (
            isinstance(self.recipient, str) and self.recipient.strip()
            and self.recipient.isprintable() and len(self.recipient) <= 80
        ):
            raise ValueError("Enter a recipient name of 1–80 printable characters.")
