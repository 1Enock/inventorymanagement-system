# Inventory Management System

This project is a simple Flask app for managing inventory items.
It stores products, lets users create and update stock, and can look up product details from the OpenFoodFacts API.

## Features

- Add, view, update, and delete inventory items
- Filter items by category
- Search items by name
- Connect to an external product database by barcode or product name
- Import product data directly into the inventory
- Use a command-line tool to interact with the app
- Run automated tests with pytest

## Project files

```bash
inventory_management_system/
├── app.py
├── models.py
├── external_api.py
├── cli.py
├── requirements.txt
├── README.md
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
└── tests/
    ├── conftest.py
    ├── test_models.py
    ├── test_routes.py
    ├── test_external_api.py
    └── test_external_routes.py
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

export FLASK_APP=app.py
flask db upgrade
flask run
```

The app runs at: http://127.0.0.1:5000

## Main API routes

- GET /api/health
- GET /api/items
- GET /api/items/<id>
- POST /api/items
- PATCH /api/items/<id>
- DELETE /api/items/<id>
- GET /api/items/search?q=term
- GET /api/external/lookup?barcode=...
- POST /api/external/import

## Example request

```bash
curl -X POST http://127.0.0.1:5000/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Peanut Butter", "category": "Pantry", "quantity": 12, "price": 4.50}'
```

## CLI usage

```bash
python cli.py list
python cli.py add --name "Peanut Butter" --category Pantry --quantity 12 --price 4.50
python cli.py show 1
python cli.py update 1 --quantity 20
python cli.py delete 1
python cli.py search --q butter
python cli.py lookup --barcode 3017624010701
python cli.py import --barcode 3017624010701 --quantity 5 --price 3.00
```

## Run tests

```bash
pytest tests/ -v
```

## Database migration

```bash
flask db migrate -m "describe your change"
flask db upgrade
```

## Notes

This project uses Flask, SQLAlchemy, SQLite, and OpenFoodFacts for live product lookup.
