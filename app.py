import os

from flask import Flask, request, jsonify
from flask_migrate import Migrate

from models import db, InventoryItem
from external_api import fetch_product_by_barcode, search_products_by_name, ExternalAPIError

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "inventory.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    Migrate(app, db)

    register_routes(app)
    return app


def register_routes(app: Flask) -> None:

    # ---------- Health check ----------
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    # ---------- CRUD: Inventory Items ----------

    @app.route("/api/items", methods=["GET"])
    def list_items():
        """List all inventory items. Optional helper filter: ?category=Snacks"""
        query = InventoryItem.query
        category = request.args.get("category")
        if category:
            query = query.filter(InventoryItem.category.ilike(category))
        items = query.order_by(InventoryItem.name).all()
        return jsonify([item.to_dict() for item in items]), 200

    @app.route("/api/items/<int:item_id>", methods=["GET"])
    def get_item(item_id):
        item = db.session.get(InventoryItem, item_id)
        if item is None:
            return jsonify({"error": "Item not found"}), 404
        return jsonify(item.to_dict()), 200

    @app.route("/api/items", methods=["POST"])
    def create_item():
        data = request.get_json(silent=True) or {}
        if not data.get("name"):
            return jsonify({"error": "'name' is required"}), 400

        item = InventoryItem(
            name=data["name"],
            barcode=data.get("barcode"),
            category=data.get("category"),
            quantity=data.get("quantity", 0),
            price=data.get("price", 0.0),
            description=data.get("description"),
            image_url=data.get("image_url"),
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201

    @app.route("/api/items/<int:item_id>", methods=["PATCH"])
    def update_item(item_id):
        item = db.session.get(InventoryItem, item_id)
        if item is None:
            return jsonify({"error": "Item not found"}), 404

        data = request.get_json(silent=True) or {}
        item.update_from_dict(data)
        db.session.commit()
        return jsonify(item.to_dict()), 200

    @app.route("/api/items/<int:item_id>", methods=["DELETE"])
    def delete_item(item_id):
        item = db.session.get(InventoryItem, item_id)
        if item is None:
            return jsonify({"error": "Item not found"}), 404

        db.session.delete(item)
        db.session.commit()
        return "", 204

    # ---------- Helper route: local search ----------

    @app.route("/api/items/search", methods=["GET"])
    def search_items():
        """Search existing inventory by partial name match: ?q=choc"""
        term = request.args.get("q", "")
        if not term:
            return jsonify({"error": "query parameter 'q' is required"}), 400
        items = InventoryItem.query.filter(InventoryItem.name.ilike(f"%{term}%")).all()
        return jsonify([item.to_dict() for item in items]), 200

    # ---------- External API integration ----------

    @app.route("/api/external/lookup", methods=["GET"])
    def external_lookup():
        """
        Look up product data from OpenFoodFacts WITHOUT saving it.
        Supports either ?barcode=... or ?name=...
        """
        barcode = request.args.get("barcode")
        name = request.args.get("name")

        if not barcode and not name:
            return jsonify({"error": "Provide either 'barcode' or 'name'"}), 400

        try:
            if barcode:
                product = fetch_product_by_barcode(barcode)
                if product is None:
                    return jsonify({"error": f"No product found for barcode {barcode}"}), 404
                return jsonify(product), 200
            else:
                results = search_products_by_name(name)
                return jsonify(results), 200
        except ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502

    @app.route("/api/external/import", methods=["POST"])
    def external_import():
        """
        Look up a product on OpenFoodFacts by barcode and save it directly
        into the inventory database. Body: {"barcode": "...", "quantity": 5, "price": 2.5}
        """
        data = request.get_json(silent=True) or {}
        barcode = data.get("barcode")
        if not barcode:
            return jsonify({"error": "'barcode' is required"}), 400

        existing = InventoryItem.query.filter_by(barcode=barcode).first()
        if existing:
            return jsonify({"error": "An item with this barcode already exists", "item": existing.to_dict()}), 409

        try:
            product = fetch_product_by_barcode(barcode)
        except ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502

        if product is None:
            return jsonify({"error": f"No product found for barcode {barcode}"}), 404

        item = InventoryItem(
            name=product["name"],
            barcode=product["barcode"],
            category=product["category"],
            description=product["description"],
            image_url=product["image_url"],
            quantity=data.get("quantity", 0),
            price=data.get("price", 0.0),
        )
        db.session.add(item)
        db.session.commit()
        return jsonify(item.to_dict()), 201


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
