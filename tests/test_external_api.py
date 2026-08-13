import pytest
import requests
import responses

from external_api import fetch_product_by_barcode, search_products_by_name, ExternalAPIError


@responses.activate
def test_fetch_product_by_barcode_found():
    responses.add(
        responses.GET,
        "https://world.openfoodfacts.org/api/v2/product/3017624010701.json",
        json={
            "status": 1,
            "product": {
                "product_name": "Nutella",
                "categories": "Spreads, Sweet spreads",
                "generic_name": "Hazelnut spread with cocoa",
                "image_front_url": "https://example.com/nutella.jpg",
            },
        },
        status=200,
    )

    product = fetch_product_by_barcode("3017624010701")

    assert product["name"] == "Nutella"
    assert product["barcode"] == "3017624010701"
    assert product["category"] == "Spreads"
    assert product["description"] == "Hazelnut spread with cocoa"
    assert product["image_url"] == "https://example.com/nutella.jpg"


@responses.activate
def test_fetch_product_by_barcode_not_found():
    responses.add(
        responses.GET,
        "https://world.openfoodfacts.org/api/v2/product/0000000000000.json",
        json={"status": 0},
        status=200,
    )

    product = fetch_product_by_barcode("0000000000000")

    assert product is None


@responses.activate
def test_fetch_product_raises_on_network_error():
    responses.add(
        responses.GET,
        "https://world.openfoodfacts.org/api/v2/product/123.json",
        body=requests.exceptions.ConnectionError("network down"),
    )

    with pytest.raises(ExternalAPIError):
        fetch_product_by_barcode("123")


@responses.activate
def test_search_products_by_name():
    responses.add(
        responses.GET,
        "https://world.openfoodfacts.org/cgi/search.pl",
        json={
            "products": [
                {"product_name": "Peanut Butter", "code": "111", "categories": "Spreads"},
                {"product_name": "Almond Butter", "code": "222", "categories": "Spreads"},
            ]
        },
        status=200,
    )

    results = search_products_by_name("butter")

    assert len(results) == 2
    assert results[0]["name"] == "Peanut Butter"
    assert results[1]["barcode"] == "222"
