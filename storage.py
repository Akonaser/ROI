"""Read and write inventory using one local JSON file."""
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from tempfile import NamedTemporaryFile

from .inventory import Batch, Inventory, Product, WasteEntry
from .validation import parse_date


def load_inventory(path):
    """Load a complete valid inventory or raise ValueError without changing the file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for collection in ("products", "batches", "waste_entries"):
            if not isinstance(data[collection], list):
                raise ValueError("Inventory collections must be lists.")
        products = [Product(**row) for row in data["products"]]
        batches = []
        for row in data["batches"]:
            expiry = parse_date(row["expiry"]) if row["expiry"] is not None else None
            batches.append(Batch(row["batch_id"], row["product_code"], expiry, row["quantity"]))
        waste_entries = [
            WasteEntry(
                row["product_code"], row["batch_id"], parse_date(row["recorded_on"]),
                row["reason"], row["quantity"], row["unit_price_sen"],
            )
            for row in data["waste_entries"]
        ]
        product_map = {product.code: product for product in products}
        batch_map = {batch.batch_id: batch for batch in batches}
        if len(product_map) != len(products) or len(batch_map) != len(batches):
            raise ValueError("Duplicate product or batch IDs.")
        for batch in batches:
            if batch.product_code not in product_map:
                raise ValueError("A batch refers to a missing product.")
        for entry in waste_entries:
            if entry.batch_id not in batch_map:
                raise ValueError("A discard refers to a missing batch.")
            batch = batch_map[entry.batch_id]
            if entry.product_code != batch.product_code:
                raise ValueError("Discard and batch product IDs differ.")
            if entry.reason == "Expired" and (batch.expiry is None or batch.expiry >= entry.recorded_on):
                raise ValueError("An expired discard has an inconsistent date.")
        return Inventory(product_map, batch_map, waste_entries)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("The inventory file contains invalid data.") from error


def save_inventory(path, inventory):
    """Replace the file only after writing the entire inventory snapshot."""
    data = {
        "products": [asdict(product) for product in inventory.products.values()],
        "batches": [asdict(batch) for batch in inventory.batches.values()],
        "waste_entries": [asdict(entry) for entry in inventory.waste_entries],
    }
    # Replace stock and waste records together after writing the whole snapshot.
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as temp:
        temp_path = Path(temp.name)
        try:
            json.dump(data, temp, indent=2, default=date.isoformat)
            temp.close()
            temp_path.replace(path)
        finally:
            temp_path.unlink(missing_ok=True)
