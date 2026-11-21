"""Validation shared by console input, desktop forms and stored records."""

from datetime import date
from decimal import Decimal
import re


def validate_integer(value, minimum=0, label="Quantity"):
    """Require a real integer within the allowed range, excluding booleans."""
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be a whole number of at least {minimum}.")
    return value


def parse_quantity(text, minimum=1):
    """Convert user-entered text to a whole quantity."""
    text = text.strip()
    if not re.fullmatch(r"[0-9]+", text):
        raise ValueError("Enter a whole number using digits 0–9.")
    try:
        quantity = int(text)
    except ValueError:
        raise ValueError("Please enter a valid whole number.") from None
    return validate_integer(quantity, minimum)


def validate_product(code, name, price_sen):
    """Check the stored identity, display name and integer-sen price."""
    if not isinstance(code, str) or not (1 <= len(code) <= 6 and code.isascii() and code.isalnum()):
        raise ValueError("Enter an ID with 1-6 letters or digits.")
    if not isinstance(name, str) or not (1 <= len(name) <= 24 and name.strip() and name.isprintable()):
        raise ValueError("Enter a printable name of 1-24 characters.")
    validate_integer(price_sen, 1, "Price in sen")
    if price_sen > 9999900:
        raise ValueError("Price must not exceed RM 99,999.00.")


def parse_price(text):
    """Return an exact integer-sen price from an RM amount."""
    text = text.strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", text):
        raise ValueError("Enter an amount such as 7 or 7.50, with up to two decimal places.")
    # Read the typed price exactly. For example, RM 7.50 becomes 750 sen for calculations.
    price = Decimal(text)
    if not Decimal("0.01") <= price <= 99999:
        raise ValueError("Price must be between RM 0.01 and RM 99,999.00.")
    return int(price * 100)


def parse_date(text):
    """Require a calendar date written exactly as YYYY-MM-DD."""
    try:
        value = date.fromisoformat(text)
        if value.isoformat() != text:
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise ValueError("Enter a valid date in YYYY-MM-DD format.") from None


def format_display_date(value):
    """Use day first on screen. Saved inventory uses ISO dates for compatibility."""
    return f"{value.day:02d} {value.month:02d} {value.year:04d}"


def parse_display_date(text):
    try:
        day, month, year = text.strip().split(" ")
        value = date(int(year), int(month), int(day))
        if format_display_date(value) == text.strip():
            return value
    except ValueError:
        pass
    raise ValueError("Enter a valid date as DD MM YYYY, for example 21 11 2026.")
