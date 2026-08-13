from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class InventoryItem(db.Model):
    """
    Represents a single product tracked in the inventory system.

    barcode is used to look up matching product data from the
    OpenFoodFacts external API.
    """

    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    barcode = db.Column(db.String(64), unique=True, nullable=True, index=True)
    category = db.Column(db.String(80), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "barcode": self.barcode,
            "category": self.category,
            "quantity": self.quantity,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_from_dict(self, data):
        """Apply a partial update (used by PATCH). Only known, present keys are touched."""
        for field in ("name", "barcode", "category", "quantity", "price", "description", "image_url"):
            if field in data:
                setattr(self, field, data[field])

    def __repr__(self):
        return f"<InventoryItem {self.id} {self.name!r}>"
