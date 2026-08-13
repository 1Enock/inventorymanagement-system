"""
Integration with the OpenFoodFacts public API.

Docs: https://openfoodfacts.github.io/openfoodfacts-server/api/

No API key is required. OpenFoodFacts asks that clients send a
descriptive User-Agent, so we set one on every request.
"""
import requests

BASE_URL = "https://world.openfoodfacts.org"
USER_AGENT = "MoringaInventoryApp/1.0 (student project; contact: keith@example.com)"
TIMEOUT_SECONDS = 8


class ExternalAPIError(Exception):
    """Raised when the OpenFoodFacts API can't be reached or returns bad data."""


def fetch_product_by_barcode(barcode: str) -> dict | None:
    """
    Look up a single product by barcode.

    Returns a normalized dict with the fields our InventoryItem cares about,
    or None if the barcode isn't found in OpenFoodFacts.
    """
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts: {exc}") from exc

    data = response.json()
    if data.get("status") != 1:
        return None

    return _normalize_product(data.get("product", {}), barcode=barcode)


def search_products_by_name(name: str, limit: int = 10) -> list[dict]:
    """
    Search OpenFoodFacts by product name (full-text search).

    Returns a list of normalized product dicts (may be empty).
    """
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit,
    }
    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts: {exc}") from exc

    data = response.json()
    products = data.get("products", [])
    return [_normalize_product(p, barcode=p.get("code")) for p in products]


def _normalize_product(product: dict, barcode: str | None) -> dict:
    """Map OpenFoodFacts' large product payload down to our inventory fields."""
    return {
        "name": product.get("product_name") or "Unnamed product",
        "barcode": barcode,
        "category": (product.get("categories") or "").split(",")[0].strip() or None,
        "description": product.get("generic_name") or product.get("ingredients_text") or None,
        "image_url": product.get("image_front_url") or product.get("image_url"),
    }
