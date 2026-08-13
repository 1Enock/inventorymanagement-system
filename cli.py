"""
Command-line interface for the Inventory Management API.

This talks to the running Flask server over HTTP — it does not
touch the database directly. Start the server first:

    flask run

Then use commands like:

    python cli.py list
    python cli.py add --name "Peanut Butter" --category Pantry --quantity 12 --price 4.50
    python cli.py show 1
    python cli.py update 1 --quantity 20
    python cli.py delete 1
    python cli.py search --q butter
    python cli.py lookup --barcode 3017624010701
    python cli.py import --barcode 3017624010701 --quantity 5 --price 3.00
"""
import click
import requests

API_BASE = "http://127.0.0.1:5000/api"


def _print_item(item: dict) -> None:
    click.echo(
        f"#{item['id']} | {item['name']} | qty={item['quantity']} | "
        f"price=${item['price']:.2f} | category={item.get('category') or '-'} | "
        f"barcode={item.get('barcode') or '-'}"
    )


@click.group()
def cli():
    """Inventory Management CLI"""


@cli.command("list")
@click.option("--category", default=None, help="Filter by category")
def list_items(category):
    """List all inventory items."""
    params = {"category": category} if category else {}
    r = requests.get(f"{API_BASE}/items", params=params)
    r.raise_for_status()
    items = r.json()
    if not items:
        click.echo("No items found.")
        return
    for item in items:
        _print_item(item)


@cli.command("show")
@click.argument("item_id", type=int)
def show_item(item_id):
    """Show a single item by ID."""
    r = requests.get(f"{API_BASE}/items/{item_id}")
    if r.status_code == 404:
        click.echo(f"No item with id {item_id}")
        return
    r.raise_for_status()
    _print_item(r.json())


@cli.command("add")
@click.option("--name", required=True)
@click.option("--barcode", default=None)
@click.option("--category", default=None)
@click.option("--quantity", default=0, type=int)
@click.option("--price", default=0.0, type=float)
@click.option("--description", default=None)
def add_item(name, barcode, category, quantity, price, description):
    """Create a new inventory item manually."""
    payload = {
        "name": name,
        "barcode": barcode,
        "category": category,
        "quantity": quantity,
        "price": price,
        "description": description,
    }
    r = requests.post(f"{API_BASE}/items", json=payload)
    r.raise_for_status()
    click.echo("Created:")
    _print_item(r.json())


@cli.command("update")
@click.argument("item_id", type=int)
@click.option("--name", default=None)
@click.option("--category", default=None)
@click.option("--quantity", default=None, type=int)
@click.option("--price", default=None, type=float)
def update_item(item_id, name, category, quantity, price):
    """Update fields on an existing item (only provided fields are changed)."""
    payload = {}
    if name is not None:
        payload["name"] = name
    if category is not None:
        payload["category"] = category
    if quantity is not None:
        payload["quantity"] = quantity
    if price is not None:
        payload["price"] = price

    if not payload:
        click.echo("Nothing to update — provide at least one field.")
        return

    r = requests.patch(f"{API_BASE}/items/{item_id}", json=payload)
    if r.status_code == 404:
        click.echo(f"No item with id {item_id}")
        return
    r.raise_for_status()
    click.echo("Updated:")
    _print_item(r.json())


@cli.command("delete")
@click.argument("item_id", type=int)
def delete_item(item_id):
    """Delete an item by ID."""
    r = requests.delete(f"{API_BASE}/items/{item_id}")
    if r.status_code == 404:
        click.echo(f"No item with id {item_id}")
        return
    r.raise_for_status()
    click.echo(f"Deleted item {item_id}")


@cli.command("search")
@click.option("--q", required=True, help="Search term for item name")
def search_items(q):
    """Search existing inventory by name."""
    r = requests.get(f"{API_BASE}/items/search", params={"q": q})
    r.raise_for_status()
    items = r.json()
    if not items:
        click.echo("No matches found.")
        return
    for item in items:
        _print_item(item)


@cli.command("lookup")
@click.option("--barcode", default=None)
@click.option("--name", default=None)
def lookup_external(barcode, name):
    """Look up a product on OpenFoodFacts without saving it."""
    if not barcode and not name:
        click.echo("Provide --barcode or --name")
        return
    params = {"barcode": barcode} if barcode else {"name": name}
    r = requests.get(f"{API_BASE}/external/lookup", params=params)
    if r.status_code != 200:
        click.echo(f"Error: {r.json().get('error')}")
        return
    data = r.json()
    if isinstance(data, list):
        for product in data:
            click.echo(f"{product['name']} | barcode={product.get('barcode') or '-'}")
    else:
        click.echo(f"{data['name']} | barcode={data.get('barcode') or '-'} | category={data.get('category') or '-'}")


@cli.command("import")
@click.option("--barcode", required=True)
@click.option("--quantity", default=0, type=int)
@click.option("--price", default=0.0, type=float)
def import_external(barcode, quantity, price):
    """Fetch a product from OpenFoodFacts by barcode and save it to inventory."""
    payload = {"barcode": barcode, "quantity": quantity, "price": price}
    r = requests.post(f"{API_BASE}/external/import", json=payload)
    if r.status_code not in (200, 201):
        click.echo(f"Error: {r.json().get('error')}")
        return
    click.echo("Imported:")
    _print_item(r.json())


if __name__ == "__main__":
    cli()
